"""Blebox sensors tests."""

import json
import pytest

from blebox_uniapi.box_types import get_latest_api_level
from .conftest import CommonEntity, DefaultBoxTest, future_date, jmerge

TEMP_CELSIUS = "celsius"
DEVICE_CLASS_TEMPERATURE = "temperature class"


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

    @property
    def native_value(self):
        """Return the state."""
        return self._feature.native_value


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

    def patch_version(apiLevel):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{ "device": {{ "apiLevel": {apiLevel} }} }}
        """

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

    DEVICE_EXTENDED_INFO_RAIN_AIR_TEMP = {}

    DEVICE_MULTISENSOR = json.loads(
        """
        {
            "multiSensor":
            {
                "sensors":
                [
                    {
                        "type": "temperature",
                        "id": 0,
                        "name": "Temperature outside",
                        "iconSet": 2,
                        "value": 3606,
                        "trend": 2,
                        "state": 2,
                        "elapsedTimeS": -1
                    },
                    {
                        "type": "temperature",
                        "id": 1,
                        "name": "Temperature inside fence",
                        "iconSet": 3,
                        "value": 4712,
                        "trend": 3,
                        "state": 2,
                        "elapsedTimeS": -1
                    },
                    {
                        "type": "temperature",
                        "id": 2,
                        "name": "Underground -10 cm",
                        "iconSet": 2,
                        "value": 2050,
                        "trend": 3,
                        "state": 2,
                        "elapsedTimeS": -1
                    }
                ]
            }
        }"""
    )

    DEVICE_MULTISENSOR_UPDATE = json.loads(
        """
        {
            "multiSensor":
            {
                "sensors":
                [
                    {
                        "type": "temperature",
                        "id": 0,
                        "name": "Temperature outside",
                        "iconSet": 2,
                        "value": 123,
                        "trend": 2,
                        "state": 2,
                        "elapsedTimeS": -1
                    },
                    {
                        "type": "temperature",
                        "id": 1,
                        "name": "Temperature inside fence",
                        "iconSet": 3,
                        "value": 213,
                        "trend": 3,
                        "state": 2,
                        "elapsedTimeS": -1
                    },
                    {
                        "type": "temperature",
                        "id": 2,
                        "name": "Underground -10 cm",
                        "iconSet": 2,
                        "value": 312,
                        "trend": 3,
                        "state": 2,
                        "elapsedTimeS": -1
                    }
                ]
            }
        }"""
    )
    DEVICE_EXTENDED_INFO = DEVICE_MULTISENSOR
    DEVICE_EXTENDED_INFO_PATH = "/state/extended"

    DEVICE_INFO_MULTISENSOR = json.loads(
        """
        {
          "device":
          {
            "deviceName": "Backyard - tempSensor PRO",
            "type": "multiSensor",
            "product": "tempSensorPro",
            "hv": "tSP-1.0",
            "fv": "0.1044",
            "universe": 0,
            "apiLevel": "20210413",
            "categories":
            [
              4,
              7
            ],
            "id": "42f5200ca102",
            "ip": "172.0.0.1",
            "availableFv": null
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
        # assert entity.outdated is False

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

    async def test_sensor_factory(self, aioclient_mock):
        """Test sensor factory method class."""

        self.DEVICE_EXTENDED_INFO = self.DEVICE_MULTISENSOR
        self.STATE_DEFAULT = self.DEVICE_MULTISENSOR
        self.DEVICE_INFO = self.DEVICE_INFO_MULTISENSOR
        await self.allow_get_info(aioclient_mock)

        entity = await self.async_entities(aioclient_mock)

        assert len(entity) == 3

    async def test_multisensor_update(self, aioclient_mock):
        self.DEV_INFO_PATH = "state"
        self.DEVICE_EXTENDED_INFO = self.DEVICE_MULTISENSOR
        self.STATE_DEFAULT = self.DEVICE_MULTISENSOR
        self.DEVICE_INFO = self.DEVICE_INFO_MULTISENSOR
        # await self.allow_get_state(aioclient_mock)

        entity = await self.updated(aioclient_mock, self.DEVICE_MULTISENSOR_UPDATE)

        assert entity.native_value == 1.2


class TestAirSensor(DefaultBoxTest):
    """Tests for sensors representing BleBox airSensor."""

    DEV_INFO_PATH = "api/air/state"

    DEVCLASS = "sensors"
    ENTITY_CLASS = BleBoxSensorEntity

    DEVICE_INFO = json.loads(
        """
    {
        "deviceName": "My air 1",
        "type": "airSensor",
        "fv": "0.973",
        "hv": "0.6",
        "apiLevel": "20180403",
        "id": "1afe34db9437",
        "ip": "192.168.1.11"
    }
    """
    )

    def patch_version(apiLevel):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{ "apiLevel": {apiLevel} }}
        """

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(future_date()))
    DEVICE_INFO_LATEST = jmerge(
        DEVICE_INFO, patch_version(get_latest_api_level("airSensor"))
    )
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20180402))

    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
        "deviceName": "My air 1",
        "type": "airSensor",
        "fv": "0.973",
        "hv": "0.6",
        "id": "1afe34db9437",
        "ip": "192.168.1.11"
    }
    """
    )

    STATE_DEFAULT = json.loads(
        """
        {
            "air": {
                "sensors": [
                    {
                        "type": "pm1",
                        "value": 49,
                        "trend": 3,
                        "state": 0,
                        "qualityLevel": 0,
                        "elaspedTimeS": -1
                    },
                    {
                        "type": "pm2.5",
                        "value": 222,
                        "trend": 1,
                        "state": 0,
                        "qualityLevel": 4,
                        "elaspedTimeS": -1
                    },
                    {
                        "type": "pm10",
                        "value": 333,
                        "trend": 0,
                        "state": 0,
                        "qualityLevel": 6,
                        "elaspedTimeS": -1
                    }
                ]
            }
        }
        """
    )

    # DEVICE_EXTENDED_INFO
    # DEVICE_EXTENDED_INFO_PATH

    async def test_init(self, aioclient_mock):
        """Test air quality sensor default state."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "My air 1 (airSensor#pm1)"
        assert entity.unique_id == "BleBox-airSensor-1afe34db9437-pm1"
        assert entity.native_value is None

    async def test_device_info(self, aioclient_mock):
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO)
        entity = (await self.async_entities(aioclient_mock))[0]
        assert entity.device_info["name"] == "My air 1"
        assert entity.device_info["mac"] == "1afe34db9437"
        assert entity.device_info["manufacturer"] == "BleBox"
        assert entity.device_info["model"] == "airSensor"
        assert entity.device_info["sw_version"] == "0.973"

    @pytest.mark.parametrize("io_param", [(0, 49), (1, 222), (2, 333)])
    async def test_update(self, aioclient_mock, io_param):
        """Test air quality sensor state after update."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[io_param[0]]

        self.allow_get_state(aioclient_mock, self.STATE_DEFAULT)
        await entity.async_update()

        assert entity.native_value == io_param[1]  # parametrised

    async def test_list_quantity(self, aioclient_mock):
        """Test air sensor init from config."""
        await self.allow_get_info(aioclient_mock)

        entity = await self.async_entities(aioclient_mock)

        assert len(entity) == 3
