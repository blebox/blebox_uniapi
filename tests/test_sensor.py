"""Blebox sensors tests."""

import json

from blebox_uniapi.box_types import get_latest_api_level

from .conftest import CommonEntity, DefaultBoxTest, future_date, jmerge

TEMP_CELSIUS = "celsius"
DEVICE_CLASS_TEMPERATURE = "temperature class"


from unittest.mock import patch
import pytest

# @pytest.fixture
# def get_entity_data():
#     with patch("blebox_uniapi.products.Products.get_entity_data", spec_set=True, autospec=True) as status_data:
#         yield status_data


def patch_version(apiLevel):
    """Generate a patch for a JSON state fixture."""
    return f"""
    {{ "device": {{ "apiLevel": {apiLevel} }} }}
    """


class BleBoxSensorEntity(CommonEntity):
    """Home Assistant representation style of a BleBox sensor feature."""

    @property
    def state(self):
        """Return the temperature."""
        return self._feature.current

    @property
    def unit_of_measurement(self):
        """Return the temperature unit."""
        return {"celsius": TEMP_CELSIUS}[self._feature.unit]

    @property
    def device_class(self):
        """Return the device class."""
        types = {"temperature": DEVICE_CLASS_TEMPERATURE}
        return types[self._feature.device_class]


class TestMultiSensor(DefaultBoxTest):
    """Tests for sensors representing BleBox multiSensor."""

    DEVCLASS = "sensors"
    ENTITY_CLASS = BleBoxSensorEntity

    DEV_INFO_PATH = "/api/device/state"
    DEVICE_INFO = json.loads(
        """
    {
        "device": {
            "deviceName":"My tempSensor PRO",
            "type":"multiSensor",
            "product":"tempSensorPro",
            "hv":"tSP-1.0",
            "fv":"0.1030",
            "universe":0,
            "apiLevel":"20210413",
            "categories":[4,7],
            "id":"12521c4f933f",
            "ip":"192.168.1.152",
            "availableFv":null
        }
    }
    """
    )
    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(future_date()))
    DEVICE_INFO_LATEST = jmerge(
        DEVICE_INFO, patch_version(get_latest_api_level("multiSensor"))
    )
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20180603))

    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
        "device": {
            "deviceName":"My tempSensor PRO",
            "type":"multiSensor",
            "product":"tempSensorPro",
            "hv":"tSP-1.0",
            "fv":"0.1030",
            "universe":0,
            "categories":[4,7],
            "id":"12521c4f933f",
            "ip":"192.168.1.152",
            "availableFv":null
        }
    }
    """
    )


    STATUS = {
        "multiSensor": {
            "sensors":[
                {"type":"temperature","id":0,"value":2368,"trend":3,"state":2,"elapsedTimeS":-1},
                {"type":"temperature","id":1,"value":2337,"trend":3,"state":2,"elapsedTimeS":-1},
                {"type":"temperature","id":2,"value":2337,"trend":3,"state":2,"elapsedTimeS":-1},
                {"type":"temperature","id":3,"value":6723,"trend":0,"state":3,"elapsedTimeS":-1}
            ]
        }
    }

    async def test_init(self, aioclient_mock, entity_data_mock):
        """Test sensor default state."""
        entity_data_mock.return_value = self.STATUS

        await self.allow_get_info(aioclient_mock)
        entities = (await self.async_entities(aioclient_mock))

        assert len(entities) == len(self.STATUS['multiSensor']['sensors'])

        for index, entity in enumerate(entities):
            assert f'-{index}.temperature' in entity.unique_id
            assert '12521c4f933f' in entity.unique_id
            assert 'multiSensor' in entity.unique_id
            assert 'BleBox' in entity.unique_id
            assert entity.unit_of_measurement == TEMP_CELSIUS
            assert entity.device_class == DEVICE_CLASS_TEMPERATURE
            assert entity.state is None

    async def test_device_info(self, aioclient_mock, entity_data_mock):
        """Test device info"""
        entity_data_mock.return_value = self.STATUS

        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.device_info["name"] == "My tempSensor PRO"
        assert entity.device_info["mac"] == "12521c4f933f"
        assert entity.device_info["manufacturer"] == "BleBox"
        assert entity.device_info["model"] == "multiSensor"
        assert entity.device_info["sw_version"] == "0.1030"


class TestTempSensor(DefaultBoxTest):
    """Tests for sensors representing BleBox tempSensor."""

    DEVCLASS = "sensors"
    ENTITY_CLASS = BleBoxSensorEntity

    DEV_INFO_PATH = "api/tempsensor/state"

    DEVICE_INFO = json.loads(
        """
    {
        "device": {
            "deviceName": "My tempSensor",
            "type": "tempSensor",
            "fv": "0.176",
            "hv": "0.6",
            "apiLevel": "20180604",
            "id": "1afe34db9437",
            "ip": "172.100.123.4"
        }
    }
    """
    )

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(future_date()))
    DEVICE_INFO_LATEST = jmerge(
        DEVICE_INFO, patch_version(get_latest_api_level("tempSensor"))
    )
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20180603))

    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
        "device": {
            "deviceName": "My tempSensor",
            "type": "tempSensor",
            "fv": "0.176",
            "hv": "0.6",
            "id": "1afe34db9437",
            "ip": "172.100.123.4"
        }
    }
    """
    )

    STATE_DEFAULT = json.loads(
        """
    {
      "tempSensor": {
        "sensors": [
          {
            "type": "temperature",
            "id": 0,
            "value": 2518,
            "trend": 3,
            "state": 2,
            "elapsedTimeS": 0
          }
        ]
      }
    }
    """
    )

    async def test_init(self, aioclient_mock):
        """Test sensor default state."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.device_class == DEVICE_CLASS_TEMPERATURE
        assert entity.unique_id == "BleBox-tempSensor-1afe34db9437-0.temperature"
        assert entity.unit_of_measurement == TEMP_CELSIUS
        assert entity.state is None

    async def test_device_info(self, aioclient_mock):
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO)
        entity = (await self.async_entities(aioclient_mock))[0]
        assert entity.device_info["name"] == "My tempSensor"
        assert entity.device_info["mac"] == "1afe34db9437"
        assert entity.device_info["manufacturer"] == "BleBox"
        assert entity.device_info["model"] == "tempSensor"
        assert entity.device_info["sw_version"] == "0.176"

    async def test_update(self, aioclient_mock):
        """Test sensor update."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        self.allow_get_state(aioclient_mock, self.STATE_DEFAULT)
        await entity.async_update()

        # TODO: include product name?
        assert entity.name == "My tempSensor (tempSensor#0.temperature)"
        assert entity.state == 25.2
