"""PyTest fixtures and test helpers."""

import copy
import json as _json
import re
from datetime import date, timedelta

import logging

from unittest.mock import AsyncMock
from deepmerge import Merger

from unittest import mock

from aiohttp import ClientResponseError, ClientSession

import pytest

from blebox_uniapi.box_types import get_latest_conf
from blebox_uniapi.session import ApiHost
from blebox_uniapi.box import Box
from blebox_uniapi.error import UnsupportedBoxVersion

_LOGGER = logging.getLogger(__name__)

retype = type(re.compile(""))


@pytest.fixture
def aioclient_mock():
    return AsyncMock(spec=ClientSession)


def array_merge(config, path, base, nxt):
    """Replace an array element with the merge result of elements."""
    if len(nxt):
        if isinstance(nxt[0], dict):
            index = 0
            for item in nxt:
                if not isinstance(item, dict):
                    raise NotImplementedError
                my_merger.merge(base[index], item)
                index += 1
            return base
        elif isinstance(nxt[0], int):
            return [nxt[0]]
        else:
            raise NotImplementedError


my_merger = Merger(
    # pass in a list of tuple, with the
    # strategies you are looking to apply
    # to each type.
    [(list, [array_merge]), (dict, ["merge"])],
    # next, choose the fallback strategies,
    # applied to all other types:
    ["override"],
    # finally, choose the strategies in
    # the case where the types conflict:
    ["override"],
)


def jmerge(base, ext):
    """Create new fixtures by adjusting existing ones."""

    result = copy.deepcopy(base)
    my_merger.merge(result, _json.loads(ext))
    return result


def future_date(delta_days=300):
    """Generate future date string in 'YYYYMMDD' format."""
    future_date = date.today() + timedelta(days=delta_days)
    return future_date.strftime("%Y%m%d")


HTTP_MOCKS = {}


def json_get_expect(mock, url, **kwargs):
    json = kwargs["json"]

    # print("json_get_expect", mock, url, "\nend:json_get_expect")
    if mock not in HTTP_MOCKS:
        HTTP_MOCKS[mock] = {}
    HTTP_MOCKS[mock][url] = json

    class EffectWhenGet:
        def __init__(self, key):
            self._key = key

        def __call__(self, url, **kwargs):
            # print("HTTP_MOCK: ",HTTP_MOCKS)
            data = HTTP_MOCKS[self._key][url]
            response = _json.dumps(data).encode("utf-8")
            status = 200
            return AiohttpClientMockResponse("GET", url, status, response)

    mock.get = AsyncMock(side_effect=EffectWhenGet(mock))


def json_post_expect(mock, url, **kwargs):
    json = kwargs["json"]
    params = kwargs["params"]

    # TODO: check
    # headers = kwargs.get("headers")
    # print("json_post_expect", mock, url, json, "\nend:json_post_expect")
    if mock not in HTTP_MOCKS:
        HTTP_MOCKS[mock] = {}
    if url not in HTTP_MOCKS[mock]:
        HTTP_MOCKS[mock][url] = {}

    HTTP_MOCKS[mock][url][params] = json

    class EffectWhenPost:
        def __init__(self, key):
            self._key = key

        def __call__(self, url, **kwargs):
            # TODO: timeout
            params = kwargs.get("data")
            print("HTTP_MOCKS:\n", HTTP_MOCKS)
            print(f"{kwargs=}")
            # TODO: better checking of params (content vs raw json)
            data = HTTP_MOCKS[self._key][url][params]
            response = _json.dumps(data).encode("utf-8")
            status = 200
            return AiohttpClientMockResponse("POST", url, status, response)

    mock.post = AsyncMock(side_effect=EffectWhenPost(mock))


class DefaultBoxTest:
    """Base class with methods common to BleBox integration tests."""

    IP = "172.0.0.1"
    LOGGER = _LOGGER

    async def async_entities(self, session):
        """Get a created entity at the given index."""

        host = self.IP
        port = 80
        timeout = 2
        api_host = ApiHost(host, port, timeout, session, None, self.LOGGER)
        product = await Box.async_from_host(api_host)
        return [
            self.ENTITY_CLASS(feature) for feature in product.features[self.DEVCLASS]
        ]

    async def allow_get_info(self, aioclient_mock, info=None):
        """Stub a HTTP GET request for the device state."""

        data = self.DEVICE_INFO if info is None else info

        json_get_expect(
            aioclient_mock, f"http://{self.IP}:80/api/device/state", json=data
        )
        if hasattr(self, "DEVICE_EXTENDED_INFO"):
            data = self.DEVICE_EXTENDED_INFO if info is None else info
            json_get_expect(
                aioclient_mock,
                f"http://{self.IP}:80{self.DEVICE_EXTENDED_INFO_PATH}",
                json=data,
            )

    def allow_get_state(self, aioclient_mock, data):
        """Stub a HTTP GET request for the product-specific state."""
        # print("allow_get_state", self.IP, self.DEV_INFO_PATH, data)
        json_get_expect(
            aioclient_mock, f"http://{self.IP}:80/{self.DEV_INFO_PATH}", json=data
        )

    def allow_get(self, aioclient_mock, api_path, data):
        """Stub a HTTP GET request."""
        json_get_expect(
            aioclient_mock, f"http://{self.IP}:80/{api_path[1:]}", json=data
        )

    async def allow_post(self, code, aioclient_mock, api_path, post_data, response):
        """Stub a HTTP POST request."""
        json_post_expect(
            aioclient_mock,
            f"http://{self.IP}:80/{api_path[1:]}",
            params=post_data,
            headers={"content-type": "application/json"},
            json=response,
        )
        await code()

    # TODO: rename?
    async def updated(self, aioclient_mock, state, index=0):
        """Return an entry on which update has already been called."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[index]

        self.allow_get_state(aioclient_mock, state)
        await entity.async_update()
        return entity

    async def test_future_version(self, aioclient_mock):
        """
        Test support for future versions, that is last supported entry in config type file.
        """
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO_FUTURE)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity._feature.product._config is get_latest_conf(
            entity._feature.product.type
        )

    async def test_latest_version(self, aioclient_mock):
        """
        Test support for latest versions, that is last supported entry in config type file.
        """
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO_LATEST)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity._feature.product._config is get_latest_conf(
            entity._feature.product.type
        )

    async def test_unsupported_version(self, aioclient_mock):
        """Test version support."""

        # only gateBox is same
        if self.DEVICE_INFO != self.DEVICE_INFO_UNSUPPORTED:
            await self.allow_get_info(aioclient_mock, self.DEVICE_INFO_UNSUPPORTED)
            with pytest.raises(UnsupportedBoxVersion):
                await self.async_entities(aioclient_mock)

    async def test_unspecified_version(self, aioclient_mock):
        """
        Test default_api_level when api level is not specified in device info.

        """
        if self.DEVICE_INFO_UNSPECIFIED_API is not None:
            await self.allow_get_info(aioclient_mock, self.DEVICE_INFO_UNSPECIFIED_API)
            with pytest.raises(UnsupportedBoxVersion):
                await self.async_entities(aioclient_mock)


class AiohttpClientMockResponse:
    """Mock Aiohttp client response."""

    def __init__(
        self, method, url, status, response, cookies=None, exc=None, headers=None
    ):
        """Initialize a fake response."""
        self.method = method
        self._url = url
        self.status = status
        self.response = response
        self.exc = exc

        self._headers = headers or {}
        self._cookies = {}

        if cookies:
            for name, data in cookies.items():
                cookie = mock.MagicMock()
                cookie.value = data
                self._cookies[name] = cookie

    @property
    def headers(self):
        return self._headers

    @property
    def cookies(self):
        return self._cookies

    @property
    def url(self):
        return self._url

    @property
    def content_type(self):
        return self._headers.get("content-type")

    async def read(self):
        return self.response

    async def text(self, encoding="utf-8"):
        return self.response.decode(encoding)

    async def json(self, encoding="utf-8"):
        return _json.loads(self.response.decode(encoding))

    async def release(self):
        pass

    def raise_for_status(self):
        """Raise error if status is 400 or higher."""
        if self.status >= 400:
            request_info = mock.Mock(real_url="http://example.com")
            # TODO: coverage
            raise ClientResponseError(
                request_info=request_info,
                history=None,
                code=self.status,
                headers=self.headers,
            )

    def close(self):
        pass


class CommonEntity:
    def __init__(self, feature):
        self._feature = feature

    @property
    def name(self):
        return self._feature.full_name

    @property
    def unique_id(self):
        return self._feature.unique_id

    async def async_update(self):
        await self._feature.async_update()

    @property
    def device_info(self):
        product = self._feature.product
        return {
            "name": product.name,
            "mac": product.unique_id,
            "manufacturer": product.brand,
            "model": product.model,
            "sw_version": product.firmware_version,
        }
