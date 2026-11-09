from typing import Any, Optional, Union

import aiohttp
import asyncio
import logging

from . import error

CONNECT_TIMEOUT = 3
CONNECT_ATTEMPTS = 2
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(
    total=None, sock_connect=CONNECT_TIMEOUT, sock_read=5
)
DEFAULT_PORT = 80

logger = logging.getLogger(__name__)


def _client_timeout(
    timeout: Union[int, aiohttp.ClientTimeout, None],
) -> aiohttp.ClientTimeout:
    if not timeout:
        return DEFAULT_TIMEOUT
    if isinstance(timeout, aiohttp.ClientTimeout):
        return timeout
    return aiohttp.ClientTimeout(total=timeout, sock_connect=CONNECT_TIMEOUT)


class ApiHost:
    def __init__(
        self,
        host: str,
        port: int,
        timeout: Union[int, aiohttp.ClientTimeout, None],
        session: Any,
        loop: Any,
        logger: logging.Logger = logger,
        **auth,
    ):
        self._host = host
        self._port = port
        self._username = auth.get("username")
        self._password = auth.get("password")
        # TODO: handle empty logger?
        self._logger = logger

        self._timeout = _client_timeout(timeout)

        self._session = session

        auth = None

        if any(data is not None for data in [self._username, self._password]):
            auth = aiohttp.BasicAuth(login=self._username, password=self._password)

        if not self._session:
            self._session = aiohttp.ClientSession(
                loop=loop, timeout=self._timeout, auth=auth
            )

        # TODO: remove?
        self._loop = loop

    async def async_request(
        self,
        path: str,
        async_method: Any,
        data: Union[dict, str, None] = None,
        allow_ota_check_response: bool = False,
    ) -> Optional[dict]:
        client_timeout = self._timeout
        url = self.api_path(path)
        kwargs: dict[str, Any] = {"timeout": client_timeout}
        if data is not None:
            kwargs["data"] = data
        try:
            response = await self._async_send(async_method, url, **kwargs)

            accepted_statuses = (200, 202, 204) if allow_ota_check_response else (200,)
            if response.status not in accepted_statuses:
                if response.status == 401:
                    raise error.UnauthorizedRequest(
                        f"Request to {url} failed with HTTP {response.status}, UNAUTHORISED"
                    )
                raise error.HttpError(
                    f"Request to {url} failed with HTTP {response.status}"
                )

            if response.content_type != "application/json":
                return None

            return await response.json()

        except aiohttp.ConnectionTimeoutError as ex:
            connect_timeout = client_timeout.sock_connect or client_timeout.connect
            raise error.TimeoutError(
                f"Failed to connect to {self.host}:{self.port} within "
                f"{connect_timeout}s ({CONNECT_ATTEMPTS} attempts)"
            ) from ex

        except asyncio.TimeoutError as ex:
            raise error.TimeoutError(f"Request to {url} timed out") from ex

        except aiohttp.ClientConnectionError as ex:
            raise error.ConnectionError(
                f"Failed to connect to {self.host}:{self.port}: {ex}"
            ) from ex

        except aiohttp.ClientError as ex:
            raise error.ClientError(f"API request {url} failed: {ex}") from ex

        except UnicodeDecodeError as ex:
            raise error.ConnectionError(
                f"Invalid response encoding from {url}: {ex}"
            ) from ex

    async def _async_send(self, async_method: Any, url: str, **kwargs: Any) -> Any:
        # Nothing was sent yet, so retrying on a new connection is safe.
        for attempt in range(1, CONNECT_ATTEMPTS):
            try:
                return await async_method(url, **kwargs)
            except aiohttp.ConnectionTimeoutError:
                self._logger.debug(
                    "Connection to %s timed out, retrying (attempt %s/%s)",
                    url,
                    attempt + 1,
                    CONNECT_ATTEMPTS,
                )
        return await async_method(url, **kwargs)

    async def async_api_get(self, path: str) -> Optional[dict]:
        try:
            return await self.async_request(path, self._session.get)
        except Exception as ex:
            logger.debug(f"EXCEPTION DURING API CALL: {ex}")
            raise ex

    async def async_api_get_ota(self, path: str) -> Optional[dict]:
        try:
            return await self.async_request(
                path, self._session.get, allow_ota_check_response=True
            )
        except Exception as ex:
            logger.debug(f"EXCEPTION DURING API CALL: {ex}")
            raise ex

    async def async_api_post(
        self, path: str, data: Union[dict, str, None]
    ) -> Optional[dict]:
        return await self.async_request(path, self._session.post, data)

    def api_path(self, path: str) -> str:
        host = self._host
        port = self._port

        # TODO: url lib
        return f"http://{host}:{port}/{path[1:]}"

    @property
    def logger(self) -> Any:
        return self._logger

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port
