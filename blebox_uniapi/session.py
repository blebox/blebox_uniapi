from typing import Any, Optional, Union

import aiohttp
import asyncio
import logging

from . import error

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=5)
DEFAULT_PORT = 80

logger = logging.getLogger(__name__)


class ApiHost:
    def __init__(
        self,
        host: str,
        port: int,
        timeout: int,
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

        self._timeout = timeout if timeout else DEFAULT_TIMEOUT

        self._session = session

        auth = None

        if any(data != None for data in [self._username, self._password]):
            auth = aiohttp.BasicAuth(login=self._username, password=self._password)

        if not self._session:
            self._session = aiohttp.ClientSession(loop=loop, timeout=timeout, auth=auth)

        # TODO: remove?
        self._loop = loop

    async def async_request(
        self, path: str, async_method: Any, data: Union[dict, str, None] = None
    ) -> Optional[dict]:
        # TODO: check timeout
        client_timeout = self._timeout
        url = self.api_path(path)
        try:
            if data is not None:
                response = await async_method(url, timeout=client_timeout, data=data)
            else:
                response = await async_method(url, timeout=client_timeout)

            if response.status != 200:
                if response.status == 401:
                    raise error.UnauthorizedRequest(
                        f"Request to {url} failed with HTTP {response.status}, UNAUTHORISED"
                    )
                raise error.HttpError(
                    f"Request to {url} failed with HTTP {response.status}"
                )

            return await response.json()

        except asyncio.TimeoutError as ex:
            raise error.TimeoutError(
                f"Failed to connect to {self.host}:{self.port} within {client_timeout}s: ({ex})"
            ) from None

        except aiohttp.ClientConnectionError as ex:
            raise error.ConnectionError(
                f"Failed to connect to {self.host}:{self.port}: {ex}"
            ) from None

        except aiohttp.ClientError as ex:
            raise error.ClientError(f"API request {url} failed: {ex}") from ex

    async def async_api_get(self, path: str) -> Optional[dict]:
        try:
            return await self.async_request(path, self._session.get)
        except Exception as ex:
            logger.error(f"EXCEPTION DURING API CALL: {ex}")
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
