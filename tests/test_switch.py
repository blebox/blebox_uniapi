from blebox_uniapi.box_types import get_latest_api_level
from .conftest import CommonEntity, DefaultBoxTest, future_date

DEVICE_CLASS_SWITCH = "switch"


class BleBoxSwitchEntity(CommonEntity):
    @property
    def device_class(self):
        return DEVICE_CLASS_SWITCH

    @property
    def is_on(self):
        return self._feature.is_on

    async def async_turn_on(self, **kwargs):
        return await self._feature.async_turn_on()

    async def async_turn_off(self, **kwargs):
        return await self._feature.async_turn_off()


class TestSwitchBox(DefaultBoxTest):
    """Tests for BleBox switchBox."""

    DEVCLASS = "switches"
    ENTITY_CLASS = BleBoxSwitchEntity

    DEV_INFO_PATH = "api/relay/state"

    DEVICE_INFO = {
        "device": {
            "deviceName": "My switchBox",
            "type": "switchBox",
            "fv": "0.247",
            "hv": "0.2",
            "id": "1afe34e750b8",
            "ip": "192.168.1.239",
            "apiLevel": "20180604",
        }
    }

    DEVICE_INFO_FUTURE = {"device": {"apiLevel": future_date()}}

    DEVICE_INFO_LATEST = {"device": {"apiLevel": get_latest_api_level("switchBox")}}

    DEVICE_INFO_UNSUPPORTED = {"device": {"apiLevel": 20180603}}

    DEVICE_INFO_UNSPECIFIED_API = {
        "device": {
            "deviceName": "My switchBox",
            "type": "switchBox",
            "fv": "0.247",
            "hv": "0.2",
            "id": "1afe34e750b8",
            "ip": "192.168.1.239",
        }
    }

    STATE_OFF = {"relays": [{"relay": 0, "state": 0, "stateAfterRestart": 0}]}

    STATE_ON = {"relays": [{"relay": 0, "state": 1, "stateAfterRestart": 0}]}

    async def test_future_version(self, aioclient_mock):
        """
        Test support for future versions, that is last supported entry in config type file.
        """
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO_FUTURE)

    async def test_latest_version(self, aioclient_mock):
        """
        Test support for latest versions, that is last supported entry in config type file.
        """
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO_LATEST)

    async def test_unsupported_version(self, aioclient_mock):
        """Test version support."""
        if self.DEVICE_INFO != self.DEVICE_INFO_UNSUPPORTED:
            await self.allow_get_info(aioclient_mock, self.DEVICE_INFO_UNSUPPORTED)

    async def test_unspecified_version(self, aioclient_mock):
        """
        Test default_api_level when api level is not specified in device info.
        """
        if self.DEVICE_INFO_UNSPECIFIED_API is not None:
            await self.allow_get_info(aioclient_mock, self.DEVICE_INFO_UNSPECIFIED_API)
