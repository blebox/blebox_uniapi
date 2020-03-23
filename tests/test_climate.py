"""BleBox climate entities tests."""
import json

from .conftest import DefaultBoxTest, jmerge, CommonEntity

# TODO: remove
SUPPORT_TARGET_TEMPERATURE = 1
HVAC_MODE_OFF = "hvac mode off"
HVAC_MODE_HEAT = "hvac mode heat"
CURRENT_HVAC_OFF = "current hvac mode off"
CURRENT_HVAC_HEAT = "current hvac mode heat"
CURRENT_HVAC_IDLE = "current hvac mode idle"
ATTR_TEMPERATURE = "temperature"
TEMP_CELSIUS = "celsius"


class ClimateDevice:
    def __init__(self):
        self._state = None

    @property
    def state(self):
        if self._feature.is_on is None:
            return None

        if not self._feature.is_on:
            return HVAC_MODE_OFF
        return HVAC_MODE_HEAT

    @property
    def device_class(self):
        return None


class BleBoxClimateEntity(CommonEntity, ClimateDevice):
    def __init__(self, feature):
        super().__init__(feature)
        ClimateDevice.__init__(self)
        pass

    """Representation of a BleBox climate feature."""

    @property
    def supported_features(self):
        """Return the supported climate features."""
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def hvac_mode(self):
        """Return the desired HVAC mode."""
        return {None: None, False: HVAC_MODE_OFF, True: HVAC_MODE_HEAT}[
            self._feature.is_on
        ]

    @property
    def hvac_action(self):
        """Return the actual current HVAC action."""
        on = self._feature.is_on
        if not on:
            return None if on is None else CURRENT_HVAC_OFF

        states = {None: None, False: CURRENT_HVAC_IDLE, True: CURRENT_HVAC_HEAT}

        heating = self._feature.is_heating
        return states[heating]

    @property
    def hvac_modes(self):
        """Return a list of possible HVAC modes."""
        return (HVAC_MODE_OFF, HVAC_MODE_HEAT)

    @property
    def temperature_unit(self):
        """Return the temperature unit."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._feature.current

    @property
    def target_temperature(self):
        """Return the desired thermostat temperature."""
        return self._feature.desired

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the climate entity mode."""
        modemap = {HVAC_MODE_OFF: "async_off", HVAC_MODE_HEAT: "async_on"}
        await getattr(self._feature, modemap[hvac_mode])()

    async def async_set_temperature(self, **kwargs):
        """Set the thermostat temperature."""
        value = kwargs[ATTR_TEMPERATURE]
        await self._feature.async_set_temperature(value)


class TestSauna(DefaultBoxTest):
    """Tests for entities representing a BleBox saunaBox."""

    DEVCLASS = "climates"
    ENTITY_CLASS = BleBoxClimateEntity

    DEV_INFO_PATH = "api/heat/state"

    DEVICE_INFO = json.loads(
        """
    {
        "device": {
            "deviceName": "My SaunaBox",
            "type": "saunaBox",
            "fv": "0.176",
            "hv": "0.6",
            "apiLevel": "20180604",
            "id": "1afe34db9437",
            "ip": "192.168.1.11"
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
            "deviceName": "My SaunaBox",
            "type": "saunaBox",
            "fv": "0.176",
            "hv": "0.6",
            "id": "1afe34db9437",
            "ip": "192.168.1.11"
        }
    }
    """
    )

    def patch_state(state, current, desired):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{
            "heat": {{
                "state": {state},
                "desiredTemp": {desired},
                "sensors": [ {{ "value": {current} }} ]
            }}
        }}
        """

    STATE_DEFAULT = json.loads(
        """
    {
        "heat": {
            "state": 0,
            "desiredTemp": 6428,
            "sensors": [
                {
                    "type": "temperature",
                    "id": 0,
                    "value": 3996,
                    "trend": 0,
                    "state": 2,
                    "elapsedTimeS": 0
                }
            ]
        }
    }
    """
    )

    STATE_OFF_BELOW = STATE_DEFAULT
    STATE_NEEDS_HEATING = jmerge(STATE_DEFAULT, patch_state(1, 2320, 3871))

    STATE_OFF_ABOVE = jmerge(STATE_DEFAULT, patch_state(0, 3871, 2876))
    STATE_NEEDS_COOLING = jmerge(STATE_DEFAULT, patch_state(1, 3871, 2876))

    STATE_REACHED = jmerge(STATE_DEFAULT, patch_state(1, 2320, 2320))
    STATE_THERMO_SET = jmerge(STATE_DEFAULT, patch_state(1, 2320, 4320))

    async def test_init(self, aioclient_mock):
        """Test default state."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "saunaBox-thermostat"
        assert entity.unique_id == "BleBox-saunaBox-1afe34db9437-thermostat"

        assert entity.device_class is None
        assert entity.supported_features & SUPPORT_TARGET_TEMPERATURE
        assert entity.hvac_modes == (HVAC_MODE_OFF, HVAC_MODE_HEAT)

        assert entity.hvac_mode is None
        assert entity.hvac_action is None
        assert entity.target_temperature is None
        assert entity.temperature_unit == TEMP_CELSIUS
        assert entity.state is None

    async def test_update(self, aioclient_mock):
        """Test updating."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert entity.hvac_mode == HVAC_MODE_OFF
        assert entity.hvac_action == CURRENT_HVAC_OFF
        assert entity.target_temperature == 64.3
        assert entity.current_temperature == 40.0
        assert entity.temperature_unit == TEMP_CELSIUS

    async def test_on_when_below_target(self, aioclient_mock):
        """Test when temperature is below desired."""

        entity = await self.updated(aioclient_mock, self.STATE_OFF_BELOW)
        assert entity.state == entity.hvac_mode == HVAC_MODE_OFF
        assert entity.hvac_action == CURRENT_HVAC_OFF

        self.allow_get(aioclient_mock, "/s/1", self.STATE_NEEDS_HEATING)
        await entity.async_set_hvac_mode(HVAC_MODE_HEAT)

        assert entity.target_temperature == 38.7
        assert entity.current_temperature == 23.2
        assert entity.state == entity.hvac_mode == HVAC_MODE_HEAT
        assert entity.hvac_action == CURRENT_HVAC_HEAT

    async def test_on_when_above_target(self, aioclient_mock):
        """Test when temperature is below desired."""

        entity = await self.updated(aioclient_mock, self.STATE_OFF_ABOVE)
        assert entity.state == entity.hvac_mode == HVAC_MODE_OFF
        assert entity.hvac_action == CURRENT_HVAC_OFF

        self.allow_get(aioclient_mock, "/s/1", self.STATE_NEEDS_COOLING)
        await entity.async_set_hvac_mode(HVAC_MODE_HEAT)

        assert entity.target_temperature == 28.8
        assert entity.current_temperature == 38.7
        assert entity.state == entity.hvac_mode == HVAC_MODE_HEAT
        assert entity.hvac_action == CURRENT_HVAC_IDLE

    async def test_on_when_at_target(self, aioclient_mock):
        """Test when temperature is below desired."""

        entity = await self.updated(aioclient_mock, self.STATE_OFF_ABOVE)
        assert entity.state == entity.hvac_mode == HVAC_MODE_OFF
        assert entity.hvac_action == CURRENT_HVAC_OFF

        self.allow_get(aioclient_mock, "/s/1", self.STATE_REACHED)
        await entity.async_set_hvac_mode(HVAC_MODE_HEAT)

        assert entity.target_temperature == 23.2
        assert entity.current_temperature == 23.2
        assert entity.state == entity.hvac_mode == HVAC_MODE_HEAT
        assert entity.hvac_action == CURRENT_HVAC_IDLE

    async def test_off(self, aioclient_mock):
        """Test turning off."""

        entity = await self.updated(aioclient_mock, self.STATE_REACHED)

        self.allow_get(aioclient_mock, "/s/0", self.STATE_OFF_BELOW)
        await entity.async_set_hvac_mode(HVAC_MODE_OFF)

        assert entity.target_temperature == 64.3
        assert entity.current_temperature == 40.0
        assert entity.state == entity.hvac_mode == HVAC_MODE_OFF
        assert entity.hvac_action == CURRENT_HVAC_OFF

    async def test_set_thermo(self, aioclient_mock):
        """Test setting thermostat."""

        entity = await self.updated(aioclient_mock, self.STATE_REACHED)
        self.allow_get(aioclient_mock, "/s/t/4321", self.STATE_THERMO_SET)
        await entity.async_set_temperature(**{ATTR_TEMPERATURE: 43.21})
        assert entity.current_temperature == 23.2  # no change yet
        assert entity.target_temperature == 43.2
        assert entity.state == entity.hvac_mode == HVAC_MODE_HEAT
        assert entity.hvac_action == CURRENT_HVAC_HEAT
