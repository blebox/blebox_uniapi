# -*- coding: utf-8 -*-

import aiohttp
import asyncio
import logging

from . import error

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=5)
DEFAULT_PORT = 80

LOGGER = logging.getLogger(__name__)


class ApiHost:
    def __init__(self, host, port, timeout, session, loop, logger=LOGGER):
        self._host = host
        self._port = port

        # TODO: handle empty logger?
        self._logger = logger

        self._timeout = timeout if timeout else DEFAULT_TIMEOUT

        self._session = session

        if not self._session:
            self._session = aiohttp.ClientSession(loop=loop, timeout=timeout)

        # TODO: remove?
        self._loop = loop

    async def async_request(self, path, async_method, data=None):
        # TODO: check timeout
        client_timeout = self._timeout

        url = self.api_path(path)

        try:
            if data is not None:
                response = await async_method(url, timeout=client_timeout, data=data)
            else:
                response = await async_method(url, timeout=client_timeout)

            if response.status != 200:
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

    async def async_api_get(self, path):
        return await self.async_request(path, self._session.get)

    async def async_api_post(self, path, data):
        return await self.async_request(path, self._session.post, data)

    def api_path(self, path):
        host = self._host
        port = self._port

        # TODO: url lib
        return f"http://{host}:{port}/{path[1:]}"

    @property
    def logger(self):
        return self._logger

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port
