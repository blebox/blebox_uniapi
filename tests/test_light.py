"""BleBox light entities tests."""
import json

from .conftest import DefaultBoxTest, jmerge, CommonEntity

from blebox_uniapi.error import UnsupportedBoxResponse, BadOnValueError

# TODO: remove
import colorsys

import pytest

# TODO: remove
ATTR_BRIGHTNESS = "brightness"
ATTR_HS_COLOR = "ATTR_HS_COLOR"
ATTR_WHITE_VALUE = "ATTR_WHITE_VALUE"
SUPPORT_BRIGHTNESS = 1
SUPPORT_COLOR = 2
SUPPORT_WHITE_VALUE = 4

# NOTE: copied from Home Assistant color util module


def rgb_hex_to_rgb_list(hex_string: str):
    """Return an RGB color value list from a hex color string."""
    return [
        int(hex_string[i: i + len(hex_string) // 3], 16)
        for i in range(0, len(hex_string), len(hex_string) // 3)
    ]


def color_hsv_to_RGB(iH: float, iS: float, iV: float):
    """Convert an hsv color into its rgb representation.

    Hue is scaled 0-360
    Sat is scaled 0-100
    Val is scaled 0-100
    """
    fRGB = colorsys.hsv_to_rgb(iH / 360, iS / 100, iV / 100)
    return (int(fRGB[0] * 255), int(fRGB[1] * 255), int(fRGB[2] * 255))


def color_hs_to_RGB(iH: float, iS: float):
    """Convert an hsv color into its rgb representation."""
    return color_hsv_to_RGB(iH, iS, 100)


def color_RGB_to_hs(iR: float, iG: float, iB: float):
    """Convert an rgb color to its hs representation."""
    return color_RGB_to_hsv(iR, iG, iB)[:2]


def color_RGB_to_hsv(iR: float, iG: float, iB: float):
    """Convert an rgb color to its hsv representation.

    Hue is scaled 0-360
    Sat is scaled 0-100
    Val is scaled 0-100
    """
    fHSV = colorsys.rgb_to_hsv(iR / 255.0, iG / 255.0, iB / 255.0)
    return round(fHSV[0] * 360, 3), round(fHSV[1] * 100, 3), round(fHSV[2] * 100, 3)


def color_rgb_to_hex(r: int, g: int, b: int) -> str:
    """Return a RGB color from a hex color string."""
    return "{0:02x}{1:02x}{2:02x}".format(round(r), round(g), round(b))


class BleBoxLightEntity(CommonEntity):
    """Representation of BleBox lights."""

    @property
    def supported_features(self):
        """Return supported features."""
        white = SUPPORT_WHITE_VALUE if self._feature.supports_white else 0
        color = SUPPORT_COLOR if self._feature.supports_color else 0
        brightness = SUPPORT_BRIGHTNESS if self._feature.supports_brightness else 0
        return white | color | brightness

    @property
    def is_on(self):
        """Return if light is on."""
        return self._feature.is_on

    @property
    def brightness(self):
        """Return the name."""
        return self._feature.brightness

    @property
    def white_value(self):
        """Return the white value."""
        return self._feature.white_value

    @property
    def hs_color(self):
        """Return the hue and saturation."""
        rgbw_hex = self._feature.rgbw_hex
        if rgbw_hex is None:
            return None

        r, g, b, x = rgb_hex_to_rgb_list(rgbw_hex)
        return color_RGB_to_hs(r, g, b)

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""

        white = kwargs.get(ATTR_WHITE_VALUE, None)
        hs_color = kwargs.get(ATTR_HS_COLOR, None)
        brightness = kwargs.get(ATTR_BRIGHTNESS, None)

        feature = self._feature
        value = feature.sensible_on_value

        if brightness is not None:
            value = feature.apply_brightness(value, brightness)

        if white is not None:
            value = feature.apply_white(value, white)

        # TODO: set via RGB
        if hs_color is not None:
            raw_rgb = color_rgb_to_hex(*color_hs_to_RGB(*hs_color))
            value = feature.apply_color(value, raw_rgb)

        # TODO: test for BadOnValueError case
        await self._feature.async_on(value)

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._feature.async_off()


class TestDimmer(DefaultBoxTest):
    """Tests for BleBox dimmerBox."""

    DEVCLASS = "lights"
    ENTITY_CLASS = BleBoxLightEntity

    DEV_INFO_PATH = "api/dimmer/state"
    DEVICE_INFO = json.loads(
        """
    {
        "device": {
            "deviceName": "My dimmer",
            "type": "dimmerBox",
            "fv": "0.247",
            "hv": "0.2",
            "id": "1afe34e750b8",
            "apiLevel": "20170829"
        },
        "network": {
            "ip": "192.168.1.239",
            "ssid": "myWiFiNetwork",
            "station_status": 5,
            "apSSID": "dimmerBox-ap",
            "apPasswd": ""
        },
        "dimmer": {
            "loadType": 7,
            "currentBrightness": 65,
            "desiredBrightness": 65,
            "temperature": 39,
            "overloaded": false,
            "overheated": false
        }
    }
    """
    )

    def patch_version(apiLevel):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{ "device": {{ "apiLevel": {apiLevel} }} }}
        """

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(20170930))
    DEVICE_INFO_LATEST = jmerge(DEVICE_INFO, patch_version(20170829))
    DEVICE_INFO_OUTDATED = jmerge(DEVICE_INFO, patch_version(20170829))

    DEVICE_INFO_MINIMUM = jmerge(DEVICE_INFO, patch_version(20170829))
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20170828))

    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
        "device": {
            "deviceName": "My dimmer",
            "type": "dimmerBox",
            "fv": "0.247",
            "hv": "0.2",
            "id": "1afe34e750b8"
        },
        "network": {
            "ip": "192.168.1.239",
            "ssid": "myWiFiNetwork",
            "station_status": 5,
            "apSSID": "dimmerBox-ap",
            "apPasswd": ""
        },
        "dimmer": {
            "loadType": 7,
            "currentBrightness": 65,
            "desiredBrightness": 65,
            "temperature": 39,
            "overloaded": false,
            "overheated": false
        }
    }
    """
    )

    STATE_DEFAULT = json.loads(
        """
    {
        "dimmer": {
            "loadType": 7,
            "currentBrightness": 11,
            "desiredBrightness": 53,
            "temperature": 29,
            "overloaded": false,
            "overheated": false
        }
    }
    """
    )

    def patch_state(current, desired):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{
            "dimmer": {{
                "currentBrightness": {current},
                "desiredBrightness": {desired}
            }}
        }}
        """

    STATE_OFF = jmerge(STATE_DEFAULT, patch_state(0, 0))
    STATE_ON_DEFAULT = jmerge(STATE_DEFAULT, patch_state(238, 254))
    STATE_ON_BRIGHT = jmerge(STATE_DEFAULT, patch_state(201, 202))

    async def test_init(self, aioclient_mock):
        """Test cover default state."""
        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "dimmerBox-brightness"
        assert entity.unique_id == "BleBox-dimmerBox-1afe34e750b8-brightness"

        assert entity.supported_features & SUPPORT_BRIGHTNESS
        assert entity.brightness == 65

        assert entity.is_on is True

    async def test_update(self, aioclient_mock):
        """Test light updating."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert entity.brightness == 53
        assert entity.is_on is True

    async def allow_set_brightness(self, code, aioclient_mock, value, response):
        """Set up mock for HTTP POST simulating brightness change."""
        await self.allow_post(
            code,
            aioclient_mock,
            "/api/dimmer/set",
            '{"dimmer":{"desiredBrightness": ' + str(value) + "}}",
            response,
        )

    async def test_on(self, aioclient_mock):
        """Test light on."""
        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

        async def turn_on():
            await entity.async_turn_on()

        await self.allow_set_brightness(
            turn_on, aioclient_mock, 255, self.STATE_ON_DEFAULT
        )

        assert entity.is_on is True
        # TODO: is max brightness a good default?
        assert entity.brightness == 254

    async def test_on_with_brightness(self, aioclient_mock):
        """Test light on with a brightness value."""
        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

        async def turn_on():
            await entity.async_turn_on(brightness=202)

        await self.allow_set_brightness(
            turn_on, aioclient_mock, 202, self.STATE_ON_BRIGHT
        )

        assert entity.is_on is True
        assert entity.brightness == 202  # as if desired brightness not reached yet

    async def test_off(self, aioclient_mock):
        """Test light off."""
        entity = await self.updated(aioclient_mock, self.STATE_ON_DEFAULT)
        assert entity.is_on is True

        async def turn_off():
            await entity.async_turn_off()

        await self.allow_set_brightness(turn_off, aioclient_mock, 0, self.STATE_OFF)

        assert entity.is_on is False
        assert entity.brightness == 0


class TestWLightBoxS(DefaultBoxTest):
    """Tests for BleBox wLightBoxS."""

    DEVCLASS = "lights"
    ENTITY_CLASS = BleBoxLightEntity

    DEV_INFO_PATH = "api/light/state"
    DEVICE_INFO = json.loads(
        """
    {
        "device": {
            "deviceName": "My wLightBoxS",
            "type": "wLightBoxS",
            "fv": "0.924",
            "hv": "0.1",
            "universe": 0,
            "id": "1afe34e750b8",
            "apiLevel": 20180718,
            "ip": "192.168.9.13",
            "availableFv": null
        }
    }
    """
    )

    def patch_version(apiLevel):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{ "device": {{ "apiLevel": {apiLevel} }} }}
        """

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(20180719))
    DEVICE_INFO_LATEST = jmerge(DEVICE_INFO, patch_version(20180718))
    DEVICE_INFO_OUTDATED = jmerge(DEVICE_INFO, patch_version(20180718))

    DEVICE_INFO_MINIMUM = jmerge(DEVICE_INFO, patch_version(20180718))
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20180717))

    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
        "device": {
            "deviceName": "My wLightBoxS",
            "type": "wLightBoxS",
            "fv": "0.247",
            "hv": "0.2",
            "id": "1afe34e750b8"
        },
        "network": {
            "ip": "192.168.1.239",
            "ssid": "myWiFiNetwork",
            "station_status": 5,
            "apSSID": "wLightBoxS-ap",
            "apPasswd": ""
        },
        "light": {
            "desiredColor": "e3",
            "currentColor": "df",
            "fadeSpeed": 255
        }
    }
    """
    )

    STATE_ON = json.loads(
        """
        {
            "light": {
                "desiredColor": "ab",
                "currentColor": "cd",
                "fadeSpeed": 255
            }
        }
    """
    )

    STATE_FULL_ON = json.loads(
        """
        {
            "light": {
                "desiredColor": "ff",
                "currentColor": "ce",
                "fadeSpeed": 255
            }
        }
    """
    )

    STATE_OFF = json.loads(
        """
        {
            "light": {
                "desiredColor": "00",
                "currentColor": "00",
                "fadeSpeed": 255
            }
        }
    """
    )

    STATE_DEFAULT = STATE_ON

    async def test_init(self, aioclient_mock):
        """Test cover default state."""
        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "wLightBoxS-color"
        assert entity.unique_id == "BleBox-wLightBoxS-1afe34e750b8-color"

        assert entity.supported_features & SUPPORT_BRIGHTNESS
        assert entity.brightness is None

        assert entity.is_on is None

    async def test_update(self, aioclient_mock):
        """Test light updating."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert entity.brightness == 0xAB
        assert entity.is_on is True

    async def allow_set_brightness(self, code, aioclient_mock, value, response):
        """Set up mock for HTTP POST simulating color change."""

        raw = "{:02X}".format(value)
        await self.allow_post(
            code,
            aioclient_mock,
            "/api/rgbw/set",
            json.dumps({"light": {"desiredColor": raw}}),
            response,
        )

    async def test_on(self, aioclient_mock):
        """Test light on."""
        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

        async def turn_on():
            await entity.async_turn_on()

        await self.allow_set_brightness(
            turn_on, aioclient_mock, 0xFF, self.STATE_FULL_ON
        )

        assert entity.is_on is True
        assert entity.brightness == 0xFF

    async def test_on_with_bad_value_type(self, aioclient_mock):
        """Test light on with off value."""
        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

        with pytest.raises(
            BadOnValueError,
            match=r"adjust_brightness called with bad parameter \(00 is <class 'str'> instead of int\)",
        ):
            await entity.async_turn_on(brightness="00")

    async def test_on_with_bad_value_exceeding_max(self, aioclient_mock):
        """Test light on with off value."""
        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

        with pytest.raises(
            BadOnValueError,
            match=r"adjust_brightness called with bad parameter \(1234 is greater than 255\)",
        ):
            await entity.async_turn_on(brightness=1234)

    async def test_off(self, aioclient_mock):
        """Test light off."""
        entity = await self.updated(aioclient_mock, self.STATE_ON)
        assert entity.is_on is True

        async def turn_off():
            await entity.async_turn_off()

        await self.allow_set_brightness(turn_off, aioclient_mock, 0, self.STATE_OFF)

        assert entity.is_on is False
        assert entity.brightness == 0


class TestWLightBox(DefaultBoxTest):
    """Tests for BleBox wLightBox."""

    DEVCLASS = "lights"
    ENTITY_CLASS = BleBoxLightEntity

    # TODO: rename everywhere (STATE_PATH)
    DEV_INFO_PATH = "api/rgbw/state"

    DEVICE_INFO = json.loads(
        """
    {
        "device": {
            "deviceName": "My light 1",
            "type": "wLightBox",
            "fv": "0.993",
            "hv": "4.3",
            "id": "1afe34e750b8",
            "apiLevel": 20190808
        }
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
    DEVICE_INFO_OUTDATED = jmerge(DEVICE_INFO, patch_version(20190807))

    DEVICE_INFO_MINIMUM = jmerge(DEVICE_INFO, patch_version(20180718))
    DEVICE_INFO_UNSUPPORTED = jmerge(DEVICE_INFO, patch_version(20180717))

    DEVICE_INFO_UNSPECIFIED_API = json.loads(
        """
    {
        "device": {
            "deviceName": "My light 1",
            "type": "wLightBox",
            "fv": "0.247",
            "hv": "0.2",
            "id": "1afe34e750b8"
        },
        "network": {
            "ip": "192.168.1.237",
            "ssid": "myWiFiNetwork",
            "station_status": 5,
            "apSSID": "wLightBox-ap",
            "apPasswd": ""
        },
        "rgbw": {
            "desiredColor": "abcdefd9",
            "currentColor": "abcdefd9",
            "fadeSpeed": 248,
            "effectSpeed": 2,
            "effectID": 3,
            "colorMode": 3
        }
    }
            """
    )

    STATE_DEFAULT = json.loads(
        """
    {
      "rgbw": {
        "colorMode": 1,
        "effectId": 2,
        "desiredColor": "fa00203A",
        "currentColor": "ff00302F",
        "lastOnColor": "f1e2d3e4",
        "durationsMs": {
          "colorFade": 1000,
          "effectFade": 1500,
          "effectStep": 2000
        }
      }
    }
    """
    )

    def patch_state(current, desired=None, last=None):
        """Generate a patch for a JSON state fixture."""

        if desired is None:
            desired = current

        return f"""
        {{
            "rgbw": {{
                "currentColor": "{current}",
                "desiredColor": "{desired}"
                { "" if last is None else f',"lastOnColor": "{last}"' }
            }}
        }}
        """

    STATE_OFF = jmerge(STATE_DEFAULT, patch_state("00000000"))
    STATE_OFF_NOLAST_WHITE = jmerge(
        STATE_DEFAULT, patch_state("0a0b0c0d", "00000000", "dacefb00")
    )
    STATE_ON = STATE_DEFAULT
    STATE_ON_AFTER_WHITE = jmerge(
        STATE_DEFAULT, patch_state("01020304", "f1e2d3c7", "f1e2d3c7")
    )
    STATE_ON_AFTER_RESET_WHITE = jmerge(
        STATE_DEFAULT, patch_state("01020304", "f1e2d300", "f1e2d300")
    )

    STATE_ON_ONLY_SOME_COLOR = jmerge(STATE_DEFAULT, patch_state("ffa1b200"))
    STATE_ON_LAST = jmerge(STATE_DEFAULT, patch_state("01020304", "f1e2d3e4"))
    STATE_AFTER_SOME_COLOR_SET = jmerge(STATE_DEFAULT, patch_state("ffa1b2e4"))

    async def test_init(self, aioclient_mock):
        """Test cover default state."""
        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "wLightBox-color"
        assert entity.unique_id == "BleBox-wLightBox-1afe34e750b8-color"

        assert entity.supported_features & SUPPORT_WHITE_VALUE
        assert entity.white_value is None

        assert entity.supported_features & SUPPORT_COLOR
        assert entity.hs_color is None
        assert entity.white_value is None

        # assert entity.supported_features & SUPPORT_BRIGHTNESS
        # assert entity.brightness == 123
        assert entity.is_on is None

    async def test_update(self, aioclient_mock):
        """Test light updating."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)
        # assert entity.brightness == 123
        assert entity.hs_color == (352.32, 100.0)
        assert entity.white_value == 0x3A
        assert entity.is_on is True  # state already available

    async def allow_set_color(self, code, aioclient_mock, value, response):
        """Set up mock for HTTP POST simulating color change."""
        await self.allow_post(
            code,
            aioclient_mock,
            "/api/rgbw/set",
            '{"rgbw":{"desiredColor": "' + str(value) + '"}}',
            response,
        )

    async def test_on_via_just_whiteness(self, aioclient_mock):
        """Test light on."""
        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

        async def action():
            await entity.async_turn_on(**{ATTR_WHITE_VALUE: 0xC7})

        await self.allow_set_color(
            action, aioclient_mock, "f1e2d3c7", self.STATE_ON_AFTER_WHITE
        )

        assert entity.is_on is True
        assert entity.white_value == 0xC7
        assert entity.hs_color == color_RGB_to_hs(0xF1, 0xE2, 0xD3)

    async def test_on_via_reset_whiteness(self, aioclient_mock):
        """Test light on."""
        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

        async def action():
            await entity.async_turn_on(**{ATTR_WHITE_VALUE: 0x0})

        await self.allow_set_color(
            action, aioclient_mock, "f1e2d300", self.STATE_ON_AFTER_RESET_WHITE
        )

        assert entity.is_on is True
        assert entity.white_value == 0x0
        assert entity.hs_color == color_RGB_to_hs(0xF1, 0xE2, 0xD3)

    async def test_on_via_just_hsl_color_with_last(self, aioclient_mock):
        """Test light on."""

        # last color: "f1e2d3e4"

        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

        input_rgb = (0xFF, 0xA1, 0xB2)
        hs_color = color_RGB_to_hs(*input_rgb)

        async def action():
            await entity.async_turn_on(**{ATTR_HS_COLOR: hs_color})

        response = self.STATE_AFTER_SOME_COLOR_SET
        await self.allow_set_color(action, aioclient_mock, "ffa0b1e4", response)

        # TODO: second part of test not needed
        assert entity.is_on is True
        assert entity.hs_color == color_RGB_to_hs(*input_rgb)
        assert entity.white_value == 0xE4

    async def test_on_via_just_hsl_color_with_no_white(self, aioclient_mock):
        """Test light on."""

        entity = await self.updated(aioclient_mock, self.STATE_OFF_NOLAST_WHITE)
        assert entity.is_on is False

        input_rgb = (0xFF, 0xA1, 0xB2)
        hs_color = color_RGB_to_hs(*input_rgb)

        async def action():
            await entity.async_turn_on(**{ATTR_HS_COLOR: hs_color})

        response = self.STATE_ON_ONLY_SOME_COLOR
        await self.allow_set_color(action, aioclient_mock, "ffa0b100", response)

        # TODO: second part of test not needed
        assert entity.is_on is True
        assert entity.hs_color == color_RGB_to_hs(*input_rgb)
        assert entity.white_value == 0x0

    async def test_on_to_last_color(self, aioclient_mock):
        """Test light on."""
        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        assert entity.is_on is False

        async def action():
            await entity.async_turn_on()

        await self.allow_set_color(
            action, aioclient_mock, "f1e2d3e4", self.STATE_ON_LAST
        )

        assert entity.is_on is True
        assert entity.white_value == 0xE4
        assert entity.hs_color == color_RGB_to_hs(0xF1, 0xE2, 0xD3)

    async def test_off(self, aioclient_mock):
        """Test light off."""
        entity = await self.updated(aioclient_mock, self.STATE_ON)
        assert entity.is_on is True

        async def action():
            await entity.async_turn_off()

        await self.allow_set_color(action, aioclient_mock, "00000000", self.STATE_OFF)

        assert entity.is_on is False
        assert entity.hs_color == (0, 0)
        assert entity.white_value == 0x00

    async def test_ancient_response(self, aioclient_mock):
        """Test e.g. unsupported, ancient device status structure."""

        DEVICE_INFO_ANCIENT_STRUCTURE = json.loads(
            """
            {
                "deviceName": "My light 1",
                "type": "wLightBox",
                "fv": "0.623",
                "hv": "0.3",
                "universe": 0,
                "id": "6201943ff9c9",
                "ip": "192.168.9.45"
            }
            """
        )

        await self.allow_get_info(aioclient_mock, DEVICE_INFO_ANCIENT_STRUCTURE)
        with pytest.raises(UnsupportedBoxResponse):
            await self.async_entities(aioclient_mock)
