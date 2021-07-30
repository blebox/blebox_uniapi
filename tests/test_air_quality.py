"""Blebox air_quality tests."""

import json

from blebox_uniapi.box_types import get_latest_api_level

from .conftest import CommonEntity, DefaultBoxTest, future_date, jmerge


class BleBoxAirQualityEntity(CommonEntity):
    """Representation of a BleBox air quality feature."""

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:blur"

    @property
    def particulate_matter_0_1(self):
        """Return the particulate matter 0.1 level."""
        return self._feature.pm1

    @property
    def particulate_matter_2_5(self):
        """Return the particulate matter 2.5 level."""
        return self._feature.pm2_5

    @property
    def particulate_matter_10(self):
        """Return the particulate matter 10 level."""
        return self._feature.pm10


class TestAirSensor(DefaultBoxTest):
    """Tests for sensors representing BleBox airSensor."""

    DEV_INFO_PATH = "api/air/state"

    DEVCLASS = "air_qualities"
    ENTITY_CLASS = BleBoxAirQualityEntity

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

    async def test_init(self, aioclient_mock):
        """Test air quality sensor default state."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "My air 1 (airSensor#0.air)"
        assert entity.icon == "mdi:blur"
        assert entity.unique_id == "BleBox-airSensor-1afe34db9437-0.air"
        assert entity.particulate_matter_0_1 is None
        assert entity.particulate_matter_2_5 is None
        assert entity.particulate_matter_10 is None

    async def test_device_info(self, aioclient_mock):
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO)
        entity = (await self.async_entities(aioclient_mock))[0]
        assert entity.device_info["name"] == "My air 1"
        assert entity.device_info["mac"] == "1afe34db9437"
        assert entity.device_info["manufacturer"] == "BleBox"
        assert entity.device_info["model"] == "airSensor"
        assert entity.device_info["sw_version"] == "0.973"

    async def test_update(self, aioclient_mock):
        """Test air quality sensor state after update."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        self.allow_get_state(aioclient_mock, self.STATE_DEFAULT)
        await entity.async_update()

        assert entity.particulate_matter_0_1 == 49
        assert entity.particulate_matter_2_5 == 222
        assert entity.particulate_matter_10 == 333
