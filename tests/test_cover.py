"""BleBox cover entities tests."""
import json

import pytest

from blebox_uniapi import error

from .conftest import DefaultBoxTest, jmerge, CommonEntity

# TODO: remove
ATTR_POSITION = "ATTR_POSITION"
DEVICE_CLASS_DOOR = "DEVICE_CLASS_DOOR"
DEVICE_CLASS_SHUTTER = "DEVICE_CLASS_SHUTTER"
STATE_CLOSED = "STATE_CLOSED"
STATE_CLOSING = "STATE_CLOSING"
STATE_OPEN = "STATE_OPEN"
STATE_OPENING = "STATE_OPENING"

SUPPORT_OPEN = 1
SUPPORT_CLOSE = 2
SUPPORT_SET_POSITION = 4
SUPPORT_STOP = 8


class BleBoxCoverEntity(CommonEntity):
    """Representation of a BleBox cover feature."""

    @property
    def state(self):
        """Return the equivalent HA cover state."""
        states = {
            None: None,
            0: STATE_CLOSING,  # moving down
            1: STATE_OPENING,  # moving up
            2: STATE_OPEN,  # manually stopped
            3: STATE_CLOSED,  # lower limit
            4: STATE_OPEN,  # upper limit / open
            # gateController
            5: STATE_OPEN,  # overload
            6: STATE_OPEN,  # motor failure
            # 7: not used
            8: STATE_OPEN,  # safety stop
        }

        return states[self._feature.state]

    @property
    def device_class(self):
        """Return the device class."""
        types = {
            "shutter": DEVICE_CLASS_SHUTTER,
            "gatebox": DEVICE_CLASS_DOOR,
            "gate": DEVICE_CLASS_DOOR,
        }
        return types[self._feature.device_class]

    # TODO: does changing this at runtime really work?
    @property
    def supported_features(self):
        """Return the supported cover features."""
        position = SUPPORT_SET_POSITION if self._feature.is_slider else 0
        stop = SUPPORT_STOP if self._feature.has_stop else 0

        return position | stop | SUPPORT_OPEN | SUPPORT_CLOSE

    @property
    def current_cover_position(self):
        """Return the current cover position."""
        current = self._invert_position(self._feature.current)
        return current if current else None

    @property
    def is_opening(self):
        """Return whether cover is opening."""
        return self._is_state(STATE_OPENING)

    @property
    def is_closing(self):
        """Return whether cover is closing."""
        return self._is_state(STATE_CLOSING)

    @property
    def is_closed(self):
        """Return whether cover is closed."""
        return self._is_state(STATE_CLOSED)

    async def async_open_cover(self, **kwargs):
        """Open the cover position."""
        await self._feature.async_open()

    async def async_close_cover(self, **kwargs):
        """Close the cover position."""
        await self._feature.async_close()

    async def async_set_cover_position(self, **kwargs):
        """Set the cover position."""
        value = kwargs[ATTR_POSITION]
        await self._feature.async_set_position(self._invert_position(value))

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self._feature.async_stop()

    def _is_state(self, state_name):
        value = self.state
        return None if value is None else value == state_name

    def _invert_position(self, position):
        # NOTE: in BleBox, 100% means 'closed'
        return None if position is None else 100 - position


class CoverTest(DefaultBoxTest):
    """Shared test helpers for Cover tests."""

    DEVCLASS = "covers"
    ENTITY_CLASS = BleBoxCoverEntity

    # TODO: refactor more
    def assert_state(self, entity, state):
        """Assert that cover state is correct."""
        assert entity.state == state

        opening, closing, closed = {
            None: [None, None, None],
            STATE_OPEN: [False, False, False],
            STATE_OPENING: [True, False, False],
            STATE_CLOSING: [False, True, False],
            STATE_CLOSED: [False, False, True],
        }[state]

        assert entity.is_opening is opening
        assert entity.is_closing is closing
        assert entity.is_closed is closed


class TestShutter(CoverTest):
    """Tests for cover devices representing a BleBox ShutterBox."""

    DEV_INFO_PATH = "api/shutter/state"

    DEVICE_INFO = json.loads(
        """
    {
        "device": {
            "deviceName": "My shutter 1",
            "type": "shutterBox",
            "fv": "0.147",
            "hv": "0.7",
            "apiLevel": "20180604",
            "id": "2bee34e750b8",
            "ip": "172.0.0.1"
        }
    }
    """
    )

    def patch_version(apiLevel):
        """Generate a patch for a JSON state fixture."""
        return f"""{{ "device": {{ "apiLevel": {apiLevel} }} }}"""

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(20190912))
    DEVICE_INFO_LATEST = jmerge(DEVICE_INFO, patch_version(20190911))
    DEVICE_INFO_OUTDATED = jmerge(DEVICE_INFO, patch_version(20190910))

    DEVICE_INFO_MINIMUM = jmerge(DEVICE_INFO, patch_version(20180604))
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20180603))

    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
        "device": {
            "deviceName": "My shutter 1",
            "type": "shutterBox",
            "fv": "0.147",
            "hv": "0.7",
            "id": "2bee34e750b8",
            "ip": "172.0.0.1"
        }
    }
    """
    )

    STATE_DEFAULT = json.loads(
        """
    {
        "shutter": {
            "state": 2,
            "currentPos": {
                "position": 34,
                "tilt": 3
            },
            "desiredPos": {
                "position": 78,
                "tilt": 97
            },
            "favPos": {
                "position": 13,
                "tilt": 17
            }
        }
    }
    """
    )

    def patch_state(state, current, desired):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{
            "shutter": {{
                "state": {state},
                "currentPos": {{ "position": {current} }},
                "desiredPos": {{ "position": {desired} }}
            }}
        }}
        """

    STATE_CLOSING = jmerge(STATE_DEFAULT, patch_state(0, 78, 100))
    STATE_CLOSED = jmerge(STATE_DEFAULT, patch_state(3, 100, 100))
    STATE_OPENING = jmerge(STATE_DEFAULT, patch_state(1, 34, 0))
    STATE_MINIMALLY_OPENING = jmerge(STATE_DEFAULT, patch_state(1, 97, 100))
    STATE_STOPPED = jmerge(STATE_DEFAULT, patch_state(2, 34, 100))
    STATE_UNKNOWN = jmerge(STATE_DEFAULT, patch_state(2, 34, -1))

    async def test_init(self, aioclient_mock):
        """Test cover default state."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "shutterBox-position"
        assert entity.unique_id == "BleBox-shutterBox-2bee34e750b8-position"

        assert entity.device_class == DEVICE_CLASS_SHUTTER

        assert entity.supported_features & SUPPORT_OPEN
        assert entity.supported_features & SUPPORT_CLOSE
        assert entity.supported_features & SUPPORT_STOP

        assert entity.supported_features & SUPPORT_SET_POSITION
        assert entity.current_cover_position is None

        # TODO: tilt
        # assert entity.supported_features & SUPPORT_SET_TILT_POSITION
        # assert entity.current_cover_tilt_position == None

        self.assert_state(entity, None)

    async def test_update(self, aioclient_mock):
        """Test cover updating."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert entity.current_cover_position == 22  # 100 - 78
        self.assert_state(entity, STATE_OPEN)

        # TODO: tilt
        # assert entity.current_tilt_position == 0

    async def test_open(self, aioclient_mock):
        """Test cover opening."""

        entity = await self.updated(aioclient_mock, self.STATE_CLOSED)
        self.assert_state(entity, STATE_CLOSED)
        self.allow_get(aioclient_mock, "/s/u", self.STATE_OPENING)
        await entity.async_open_cover()
        self.assert_state(entity, STATE_OPENING)

    async def test_close(self, aioclient_mock):
        """Test cover closing."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)
        self.assert_state(entity, STATE_OPEN)
        self.allow_get(aioclient_mock, "/s/d", self.STATE_CLOSING)
        await entity.async_close_cover()
        self.assert_state(entity, STATE_CLOSING)

    async def test_set_position(self, aioclient_mock):
        """Test cover position setting."""

        entity = await self.updated(aioclient_mock, self.STATE_CLOSED)
        self.assert_state(entity, STATE_CLOSED)
        self.allow_get(aioclient_mock, "/s/p/99", self.STATE_MINIMALLY_OPENING)
        await entity.async_set_cover_position(**{ATTR_POSITION: 1})  # almost closed
        self.assert_state(entity, STATE_OPENING)

    async def test_stop(self, aioclient_mock):
        """Test cover stopping."""

        entity = await self.updated(aioclient_mock, self.STATE_OPENING)
        self.assert_state(entity, STATE_OPENING)
        self.allow_get(aioclient_mock, "/s/s", self.STATE_STOPPED)
        await entity.async_stop_cover()
        self.assert_state(entity, STATE_OPEN)

    async def test_unkown_position(self, aioclient_mock):
        """Test handling cover at unknown position."""
        entity = await self.updated(aioclient_mock, self.STATE_UNKNOWN)
        self.assert_state(entity, STATE_OPEN)


class TestGateBox(CoverTest):
    """Tests for cover devices representing a BleBox gateBox."""

    DEV_INFO_PATH = "api/gate/state"

    # TODO: does gateBox have an api level currently?
    DEVICE_INFO = json.loads(
        """
        {
            "deviceName": "My gate 1",
            "type": "gateBox",
            "fv": "0.176",
            "hv": "0.6",
            "id": "1afe34db9437",
            "ip": "192.168.1.11"
        }
        """
    )

    DEVICE_INFO_FUTURE = DEVICE_INFO
    DEVICE_INFO_LATEST = DEVICE_INFO
    DEVICE_INFO_OUTDATED = DEVICE_INFO
    DEVICE_INFO_MINIMUM = DEVICE_INFO
    DEVICE_INFO_UNSUPPORTED = DEVICE_INFO

    DEVICE_INFO_UNSPECIFIED_API = None  # already handled as default case

    STATE_DEFAULT = json.loads(
        """
        {
            "currentPos": 50,
            "desiredPos": 50,
            "extraButtonType": 1,
            "extraButtonRelayNumber": 1,
            "extraButtonPulseTimeMs": 800,
            "extraButtonInvert": 1,
            "gateType": 0,
            "gateRelayNumber": 0,
            "gatePulseTimeMs": 800,
            "gateInvert": 0,
            "inputsType": 1,
            "openLimitSwitchInputNumber": 0,
            "closeLimitSwitchInputNumber": 1
        }
    """
    )

    STATE_CLOSED = jmerge(STATE_DEFAULT, '{ "currentPos": 0, "desiredPos": 0 }')
    STATE_OPENING = jmerge(STATE_DEFAULT, '{ "currentPos": 50, "desiredPos": 100 }')
    STATE_CLOSING = jmerge(STATE_DEFAULT, '{ "currentPos": 50, "desiredPos": 0 }')
    STATE_STOPPED = jmerge(STATE_DEFAULT, '{ "currentPos": 50, "desiredPos": 50 }')
    STATE_FULLY_OPENED = jmerge(
        STATE_DEFAULT, '{ "currentPos": 100, "desiredPos": 100 }'
    )

    STATE_OPENING_NO_STOP = jmerge(STATE_OPENING, '{ "extraButtonType": 3}')

    async def test_init(self, aioclient_mock):
        """Test cover default state."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "gateBox-position"
        assert entity.unique_id == "BleBox-gateBox-1afe34db9437-position"
        assert entity.device_class == DEVICE_CLASS_DOOR
        assert entity.supported_features & SUPPORT_OPEN
        assert entity.supported_features & SUPPORT_CLOSE

        # Not available since requires fetching state to detect
        assert not entity.supported_features & SUPPORT_STOP

        assert not entity.supported_features & SUPPORT_SET_POSITION
        assert entity.current_cover_position is None
        self.assert_state(entity, None)

    async def test_update(self, aioclient_mock):
        """Test cover updating."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert entity.current_cover_position == 50  # 100 - 34
        self.assert_state(entity, STATE_OPEN)

    async def test_open(self, aioclient_mock):
        """Test cover opening."""

        entity = await self.updated(aioclient_mock, self.STATE_CLOSED)
        assert entity.state == STATE_CLOSED
        self.assert_state(entity, STATE_CLOSED)
        self.allow_get(aioclient_mock, "/s/p", self.STATE_OPENING)
        await entity.async_open_cover()
        self.assert_state(entity, STATE_OPENING)

    async def test_fully_opened(self, aioclient_mock):
        entity = await self.updated(aioclient_mock, self.STATE_FULLY_OPENED)
        assert entity.state == STATE_OPEN

    async def test_close(self, aioclient_mock):
        """Test cover closing."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)
        self.assert_state(entity, STATE_OPEN)
        self.allow_get(aioclient_mock, "/s/p", self.STATE_CLOSING)
        await entity.async_close_cover()
        self.assert_state(entity, STATE_CLOSING)

    async def test_closed(self, aioclient_mock):
        """Test cover closed state."""

        entity = await self.updated(aioclient_mock, self.STATE_CLOSED)
        self.assert_state(entity, STATE_CLOSED)

    async def test_stop(self, aioclient_mock):
        """Test cover stopping."""

        entity = await self.updated(aioclient_mock, self.STATE_OPENING)
        self.assert_state(entity, STATE_OPENING)
        self.allow_get(aioclient_mock, "/s/s", self.STATE_STOPPED)
        await entity.async_stop_cover()
        self.assert_state(entity, STATE_OPEN)

    async def test_with_stop(self, aioclient_mock):
        """Test stop capability is available."""

        entity = await self.updated(aioclient_mock, self.STATE_OPENING)
        assert entity.supported_features & SUPPORT_STOP

    async def test_with_no_stop(self, aioclient_mock):
        """Test stop capability is not available."""

        entity = await self.updated(aioclient_mock, self.STATE_OPENING_NO_STOP)
        assert not entity.supported_features & SUPPORT_STOP

    async def test_stop_with_no_stop(self, aioclient_mock):
        """Test stop capability is not available."""

        entity = await self.updated(aioclient_mock, self.STATE_OPENING_NO_STOP)

        with pytest.raises(
            error.MisconfiguredDevice, match=r"second button not configured as 'stop'"
        ):
            await entity.async_stop_cover()


class TestGateController(CoverTest):
    """Tests for cover devices representing a BleBox gateController."""

    DEV_INFO_PATH = "api/gatecontroller/state"

    DEVICE_INFO = json.loads(
        """
    {
      "device": {
        "deviceName": "My gate controller 1",
        "type": "gateController",
        "apiLevel": "20180604",
        "fv": "1.390",
        "hv": "custom.2.6",
        "id": "0ff2ffaafe30db9437",
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

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(20190912))
    DEVICE_INFO_LATEST = jmerge(DEVICE_INFO, patch_version(20190911))
    DEVICE_INFO_OUTDATED = jmerge(DEVICE_INFO, patch_version(20190910))

    DEVICE_INFO_MINIMUM = jmerge(DEVICE_INFO, patch_version(20180604))
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20180603))

    # NOTE: can't happen with a real device
    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
      "device": {
        "deviceName": "My gate controller 1",
        "type": "gateController",
        "fv": "1.390",
        "hv": "custom.2.6",
        "id": "0ff2ffaafe30db9437",
        "ip": "192.168.1.11"
      }
    }
    """
    )

    STATE_DEFAULT = json.loads(
        """
    {
        "gateController": {
            "state": 2,
            "safety": {
                "eventReason": 0,
                "triggered": [ 0 ]
            },
            "currentPos": [ 31 ],
            "desiredPos": [ 29 ]
        }
    }
    """
    )

    def patch_state(state, current, desired):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{
            "gateController": {{
                "state": {state},
                "currentPos": [ {current} ],
                "desiredPos": [ {desired} ]
            }}
        }}
        """

    STATE_CLOSED = jmerge(STATE_DEFAULT, patch_state(3, 100, 100))
    STATE_OPENING = jmerge(STATE_DEFAULT, patch_state(1, 34, 0))
    STATE_CLOSING = jmerge(STATE_DEFAULT, patch_state(0, 78, 100))
    STATE_MINIMALLY_OPENING = jmerge(STATE_DEFAULT, patch_state(1, 97, 100))
    STATE_STOPPED = jmerge(STATE_DEFAULT, patch_state(2, 34, 100))

    async def test_init(self, aioclient_mock):
        """Test cover default state."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "gateController-position"
        assert entity.unique_id == "BleBox-gateController-0ff2ffaafe30db9437-position"

        assert entity.device_class == DEVICE_CLASS_DOOR

        assert entity.supported_features & SUPPORT_OPEN
        assert entity.supported_features & SUPPORT_CLOSE
        assert entity.supported_features & SUPPORT_STOP

        assert entity.supported_features & SUPPORT_SET_POSITION
        assert entity.current_cover_position is None
        self.assert_state(entity, None)

    async def test_update(self, aioclient_mock):
        """Test cover updating."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert entity.current_cover_position == 71  # 100 - 29
        self.assert_state(entity, STATE_OPEN)

    async def test_open(self, aioclient_mock):
        """Test cover opening."""

        entity = await self.updated(aioclient_mock, self.STATE_CLOSED)
        self.assert_state(entity, STATE_CLOSED)
        self.allow_get(aioclient_mock, "/s/o", self.STATE_OPENING)
        await entity.async_open_cover()
        self.assert_state(entity, STATE_OPENING)

    async def test_close(self, aioclient_mock):
        """Test cover closing."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)
        self.assert_state(entity, STATE_OPEN)
        self.allow_get(aioclient_mock, "/s/c", self.STATE_CLOSING)
        await entity.async_close_cover()
        self.assert_state(entity, STATE_CLOSING)

    async def test_set_position(self, aioclient_mock):
        """Test cover position setting."""

        entity = await self.updated(aioclient_mock, self.STATE_CLOSED)
        self.assert_state(entity, STATE_CLOSED)
        self.allow_get(aioclient_mock, "/s/p/99", self.STATE_MINIMALLY_OPENING)
        await entity.async_set_cover_position(**{ATTR_POSITION: 1})  # almost closed
        self.assert_state(entity, STATE_OPENING)

    async def test_stop(self, aioclient_mock):
        """Test cover stopping."""

        entity = await self.updated(aioclient_mock, self.STATE_OPENING)
        self.assert_state(entity, STATE_OPENING)
        self.allow_get(aioclient_mock, "/s/s", self.STATE_STOPPED)
        await entity.async_stop_cover()
        self.assert_state(entity, STATE_OPEN)
