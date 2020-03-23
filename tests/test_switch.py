"""Blebox switch tests."""

import json

from .conftest import DefaultBoxTest, jmerge, CommonEntity

DEVICE_CLASS_SWITCH = "switch"


class BleBoxSwitchEntity(CommonEntity):
    @property
    def device_class(self):
        types = {"relay": DEVICE_CLASS_SWITCH}
        return types[self._feature.device_class]

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

    DEVICE_INFO = json.loads(
        """
    {
        "device":   {
            "deviceName": "My switchBox",
            "type": "switchBox",
            "fv": "0.247",
            "hv": "0.2",
            "id": "1afe34e750b8",
            "ip": "192.168.1.239",
            "apiLevel": "20190808"
        }
    }
    """
    )

    def patch_version(apiLevel):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{ "device": {{ "apiLevel": {apiLevel} }} }}
        """

    # TODO: make future far off to make tests less brittle?
    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(20190809))
    DEVICE_INFO_LATEST = jmerge(DEVICE_INFO, patch_version(20190808))
    DEVICE_INFO_OUTDATED = jmerge(DEVICE_INFO, patch_version(20190807))
    DEVICE_INFO_MINIMUM = jmerge(DEVICE_INFO, patch_version(20180604))
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20180603))

    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
        "device":   {
            "deviceName": "My switchBox",
            "type": "switchBox",
            "fv": "0.247",
            "hv": "0.2",
            "id": "1afe34e750b8",
            "ip": "192.168.1.239"
        }
    }
    """
    )

    STATE_DEFAULT = json.loads(
        """
        {
            "relays": [{
                "relay": 0,
                "state": 0,
                "stateAfterRestart": 0
            } ]
        }
        """
    )

    def patch_state(state):
        """Generate a patch for a JSON state fixture."""
        return f'{{"relays": [ {{ "state": {state} }} ]}}'

    STATE_OFF = STATE_DEFAULT
    STATE_ON = jmerge(STATE_DEFAULT, patch_state(1))

    async def test_init(self, aioclient_mock):
        """Test switch default state."""

        await self.allow_get_info(aioclient_mock)

        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "switchBox-0.relay"
        assert entity.unique_id == "BleBox-switchBox-1afe34e750b8-0.relay"

        assert entity.device_class == DEVICE_CLASS_SWITCH

        assert entity.is_on is None

    async def test_update_when_off(self, aioclient_mock):
        """Test switch updating when off."""

        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

    async def test_update_when_on(self, aioclient_mock):
        """Test switch updating when on."""

        entity = await self.updated(aioclient_mock, self.STATE_ON)
        assert entity.is_on is True

    async def test_on(self, aioclient_mock):
        """Test turning switch on."""

        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        self.allow_get(aioclient_mock, "/s/1", self.STATE_ON)
        await entity.async_turn_on()
        assert entity.is_on is True

    async def test_off(self, aioclient_mock):
        """Test turning switch off."""

        entity = await self.updated(aioclient_mock, self.STATE_ON)
        self.allow_get(aioclient_mock, "/s/0", self.STATE_OFF)
        await entity.async_turn_off()
        assert entity.is_on is False


class TestSwitchBoxD(DefaultBoxTest):
    """Tests for BleBox switchBoxD."""

    DEVCLASS = "switches"
    ENTITY_CLASS = BleBoxSwitchEntity

    DEV_INFO_PATH = "api/relay/state"

    DEVICE_INFO = json.loads(
        """
    {
        "device": {
            "deviceName": "My switchBoxD",
            "type": "switchBoxD",
            "fv": "0.200",
            "hv": "0.7",
            "id": "1afe34e750b8",
            "apiLevel": "20190808"
        }
    }
    """
    )

    STATE_DEFAULT = json.loads(
        """
        {
            "relays": [
            {
                "relay": 0,
                "state": 0,
                "stateAfterRestart": 0,
                "name": "output 1"
            },
            {
                "relay": 1,
                "state": 0,
                "stateAfterRestart": 0,
                "name": "output 2"
            }
            ]
        }
        """
    )

    def patch_version(apiLevel):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{ "device": {{ "apiLevel": {apiLevel} }} }}
        """

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(20190809))
    DEVICE_INFO_LATEST = jmerge(DEVICE_INFO, patch_version(20190808))
    DEVICE_INFO_OUTDATED = jmerge(DEVICE_INFO, patch_version(20190808))
    DEVICE_INFO_MINIMUM = jmerge(DEVICE_INFO, patch_version(20190808))
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20190807))

    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
        "device": {
            "deviceName": "My switchBoxD",
            "type": "switchBoxD",
            "fv": "0.200",
            "hv": "0.7",
            "id": "1afe34e750b8"
        }
    }
    """
    )

    def patch_state(state1, state2):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{
            "relays": [
            {{ "state": {state1} }},
            {{ "state": {state2} }}
            ]
        }}
        """

    STATE_BOTH_OFF = STATE_DEFAULT
    STATE_FIRST_ON = jmerge(STATE_DEFAULT, patch_state(1, 0))
    STATE_SECOND_ON = jmerge(STATE_DEFAULT, patch_state(0, 1))
    STATE_BOTH_ON = jmerge(STATE_DEFAULT, patch_state(1, 1))

    async def test_init(self, aioclient_mock):
        """Test switch default state."""

        await self.allow_get_info(aioclient_mock)
        entities = await self.async_entities(aioclient_mock)

        entity = entities[0]
        # TODO: include output names?
        assert entity.name == "switchBoxD-0.relay"
        assert entity.unique_id == "BleBox-switchBoxD-1afe34e750b8-0.relay"
        assert entity.device_class == DEVICE_CLASS_SWITCH
        assert entity.is_on is None

        entity = entities[1]
        assert entity.name == "switchBoxD-1.relay"
        assert entity.unique_id == "BleBox-switchBoxD-1afe34e750b8-1.relay"
        assert entity.device_class == DEVICE_CLASS_SWITCH
        assert entity.is_on is None

    async def test_update_when_off(self, aioclient_mock):
        """Test switch updating when off."""

        await self.allow_get_info(aioclient_mock)
        entities = await self.async_entities(aioclient_mock)

        self.allow_get_state(aioclient_mock, self.STATE_BOTH_OFF)

        # updating any one is fine
        await entities[0].async_update()

        assert entities[0].is_on is False
        assert entities[1].is_on is False

    async def test_update_when_second_off(self, aioclient_mock):
        """Test switch updating when off."""

        await self.allow_get_info(aioclient_mock)
        entities = await self.async_entities(aioclient_mock)

        self.allow_get_state(aioclient_mock, self.STATE_FIRST_ON)

        # updating any one is fine
        await entities[0].async_update()

        assert entities[0].is_on is True
        assert entities[1].is_on is False

    async def test_first_on(self, aioclient_mock):
        """Test turning switch on."""

        await self.allow_get_info(aioclient_mock)
        entities = await self.async_entities(aioclient_mock)

        self.allow_get(aioclient_mock, "/s/0/1", self.STATE_FIRST_ON)
        await entities[0].async_turn_on()
        assert entities[0].is_on is True
        assert entities[1].is_on is False

    async def test_second_on(self, aioclient_mock):
        """Test turning switch on."""

        await self.allow_get_info(aioclient_mock)
        entities = await self.async_entities(aioclient_mock)

        self.allow_get(aioclient_mock, "/s/1/1", self.STATE_SECOND_ON)
        await entities[1].async_turn_on()
        assert entities[0].is_on is False
        assert entities[1].is_on is True

    async def test_first_off(self, aioclient_mock):
        """Test turning switch on."""

        await self.allow_get_info(aioclient_mock)
        entities = await self.async_entities(aioclient_mock)

        self.allow_get_state(aioclient_mock, self.STATE_BOTH_ON)
        await entities[0].async_update()

        self.allow_get(aioclient_mock, "/s/0/0", self.STATE_SECOND_ON)
        await entities[0].async_turn_off()
        assert entities[0].is_on is False
        assert entities[1].is_on is True

    async def test_second_off(self, aioclient_mock):
        """Test turning switch on."""

        await self.allow_get_info(aioclient_mock)
        entities = await self.async_entities(aioclient_mock)

        self.allow_get_state(aioclient_mock, self.STATE_BOTH_ON)
        await entities[0].async_update()

        self.allow_get(aioclient_mock, "/s/1/0", self.STATE_FIRST_ON)
        await entities[1].async_turn_off()
        assert entities[0].is_on is True
        assert entities[1].is_on is False
