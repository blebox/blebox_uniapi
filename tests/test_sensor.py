"""Blebox sensors tests."""

import json

from .conftest import DefaultBoxTest, CommonEntity, jmerge

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

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(20180605))
    DEVICE_INFO_LATEST = jmerge(DEVICE_INFO, patch_version(20180604))
    DEVICE_INFO_OUTDATED = jmerge(DEVICE_INFO, patch_version(20180604))
    DEVICE_INFO_MINIMUM = jmerge(DEVICE_INFO, patch_version(20180604))
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
        assert entity.outdated is False

    async def test_update(self, aioclient_mock):
        """Test sensor update."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        self.allow_get_state(aioclient_mock, self.STATE_DEFAULT)
        await entity.async_update()

        # TODO: include product name?
        assert entity.name == "tempSensor-0.temperature"
        assert entity.state == 25.2
