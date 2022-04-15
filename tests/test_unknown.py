import pytest

from blebox_uniapi.session import ApiHost
from blebox_uniapi.box import Box
from blebox_uniapi import error

from .conftest import json_get_expect


@pytest.fixture
def data():
    return {
        "id": "abcd1234ef",
        "type": "unknownBox",
        "deviceName": "foobar",
        "fv": "1.23",
        "hv": "4.56",
        "apiLevel": "20180403",
    }


class TestUnknownDevice:
    async def test_unknown_product(self, aioclient_mock, data):
        host = "172.1.2.3"
        with pytest.raises(error.UnsupportedBoxResponse, match=r"unknownBox"):
            full_data = {"device": data}
            json_get_expect(
                aioclient_mock, f"http://{host}:80/api/device/state", json=full_data
            )

            port = 80
            timeout = 2
            api_host = ApiHost(host, port, timeout, aioclient_mock, None, None)
            await Box.async_from_host(api_host)

    async def test_unknown_product_without_device_section(self, aioclient_mock, data):
        host = "172.1.2.3"
        with pytest.raises(error.UnsupportedBoxResponse, match=r"unknownBox"):
            json_get_expect(
                aioclient_mock, f"http://{host}:80/api/device/state", json=data
            )

            port = 80
            timeout = 2
            api_host = ApiHost(host, port, timeout, aioclient_mock, None, None)
            await Box.async_from_host(api_host)

    async def test_unknown_product_without_device_and_type(self, aioclient_mock, data):
        host = "172.1.2.3"
        with pytest.raises(error.UnsupportedBoxResponse, match=r"has no type"):
            del data["type"]
            json_get_expect(
                aioclient_mock, f"http://{host}:80/api/device/state", json=data
            )

            port = 80
            timeout = 2
            api_host = ApiHost(host, port, timeout, aioclient_mock, None, None)
            await Box.async_from_host(api_host)
