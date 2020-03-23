# -*- coding: utf-8 -*-

import aiohttp

from . import error

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=5)
DEFAULT_PORT = 80


class ApiHost:
    def __init__(self, host, port, timeout, session, loop, logger):
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

        url = self.api_path(path)

        try:
            # TODO: check timeout
            client_timeout = self._timeout
            if data is not None:
                response = await async_method(url, timeout=client_timeout, data=data)
            else:
                response = await async_method(url, timeout=client_timeout)

            if response.status != 200:
                raise error.HttpError(f"Http error: {response.status}")

            return await response.json()

        # TODO: just log errors instead?
        except aiohttp.ServerTimeoutError:
            raise error.TimeoutError("Timeout trying to connect")

        except aiohttp.ClientError as ex:
            self._logger.debug("ERR: %s", ex)
            raise error.ClientError("Client Error: %s", ex)

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
