"""BleBox light entities tests."""
import json

from .conftest import CommonEntity, DefaultBoxTest, future_date, jmerge

from blebox_uniapi.box_types import get_latest_api_level
from blebox_uniapi.error import BadOnValueError, UnsupportedBoxVersion
from blebox_uniapi.light import Light

# TODO: remove
import colorsys

import pytest

# TODO: remove
ATTR_BRIGHTNESS = "brightness"
ATTR_HS_COLOR = "ATTR_HS_COLOR"
ATTR_WHITE_VALUE = "ATTR_WHITE_VALUE"
ATTR_RGB_COLOR = "rgb_color"
ATTR_RGBW_COLOR = "rgbw_color"
ATTR_EFFECT = "effect"
ATTR_COLOR_TEMP = "color_temp"
ATTR_RGBWW_COLOR = "rgbww_color"
SUPPORT_BRIGHTNESS = 1
SUPPORT_COLOR = 2
SUPPORT_WHITE_VALUE = 4
COLOR_MODE_BRIGHTNESS = "brightness"
COLOR_MODE_COLOR_TEMP = "color_temp"
COLOR_MODE_ONOFF = "onoff"
COLOR_MODE_RGB = "rgb"
COLOR_MODE_RGBW = "rgbw"
COLOR_MODE_RGBWW = "rgbww"

COLOR_MODE_MAP = {
    1: COLOR_MODE_RGBW,
    2: COLOR_MODE_RGB,
    3: COLOR_MODE_BRIGHTNESS,
    4: COLOR_MODE_RGBW,
    # RGB and Brightness 2 and 3 implementation difference, if W hex is not null only this or RGB + Brightness separated with mask
    5: COLOR_MODE_COLOR_TEMP,
    6: COLOR_MODE_COLOR_TEMP,  # two instances
    7: COLOR_MODE_RGBWW,
}

# NOTE: copied from Home Assistant color util module


def rgb_hex_to_rgb_list(hex_string: str):
    """Return an RGB color value list from a hex color string."""
    return [
        int(hex_string[i : i + len(hex_string) // 3], 16)
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
    def is_on(self) -> bool:
        """Return if light is on."""
        return self._feature.is_on

    @property
    def brightness(self):
        """Return the brightness."""
        return self._feature.brightness

    @property
    def color_temp(self):
        """Return color temperature."""
        return self._feature.color_temp

    @property
    def color_mode(self):
        """Return the color mode. Set values to _attr_ibutes if needed."""
        color_mode_tmp = COLOR_MODE_MAP.get(self._feature.color_mode, COLOR_MODE_ONOFF)
        if color_mode_tmp == COLOR_MODE_COLOR_TEMP:
            self._attr_min_mireds = 1
            self._attr_max_mireds = 255

        return color_mode_tmp

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return self._feature.effect_list

    @property
    def effect(self):
        """Return the current effect."""
        return self._feature.effect

    @property
    def rgb_color(self):
        """Return value for rgb."""
        if (rgb_hex := self._feature.rgb_hex) is None:
            return None
        return tuple(
            self._feature.normalise_elements_of_rgb(
                self._feature.rgb_hex_to_rgb_list(rgb_hex)[0:3]
            )
        )

    @property
    def rgbw_color(self):
        """Return the hue and saturation."""
        if (rgbw_hex := self._feature.rgbw_hex) is None:
            return None
        return tuple(self._feature.rgb_hex_to_rgb_list(rgbw_hex)[0:4])

    @property
    def rgbww_color(self):
        """Return value for rgbww."""
        if (rgbww_hex := self._feature.rgbww_hex) is None:
            return None
        return tuple(self._feature.rgb_hex_to_rgb_list(rgbww_hex))

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        print("async_turn_on:", kwargs)
        rgbw = kwargs.get(ATTR_RGBW_COLOR)
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        effect = kwargs.get(ATTR_EFFECT)
        color_temp = kwargs.get(ATTR_COLOR_TEMP)
        rgbww = kwargs.get(ATTR_RGBWW_COLOR)
        feature = self._feature
        value = feature.sensible_on_value
        rgb = kwargs.get(ATTR_RGB_COLOR)

        if rgbw is not None:
            value = list(rgbw)
        if color_temp is not None:
            value = feature.return_color_temp_with_brightness(
                int(color_temp), self.brightness
            )

        if rgbww is not None:
            value = list(rgbww)

        if rgb is not None:
            if self.color_mode == COLOR_MODE_RGB and brightness is None:
                brightness = self.brightness
            value = list(rgb)

        if brightness is not None:
            if self.color_mode == ATTR_COLOR_TEMP:
                value = feature.return_color_temp_with_brightness(
                    self.color_temp, brightness
                )
            else:
                value = feature.apply_brightness(value, brightness)

        if effect is not None:
            effect_value = self.effect_list.index(effect)
            await self._feature.async_api_command("effect", effect_value)
        else:
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

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(future_date()))
    DEVICE_INFO_LATEST = jmerge(
        DEVICE_INFO, patch_version(get_latest_api_level("dimmerBox"))
    )
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
    STATE_ON_DEFAULT = jmerge(STATE_DEFAULT, patch_state(238, 255))
    STATE_ON_BRIGHT = jmerge(STATE_DEFAULT, patch_state(201, 202))

    async def test_init(self, aioclient_mock):
        """Test cover default state."""
        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "My dimmer (dimmerBox#brightness)"
        assert entity.unique_id == "BleBox-dimmerBox-1afe34e750b8-brightness"

        # assert entity.supported_features & SUPPORT_BRIGHTNESS
        assert entity.brightness is None

        assert entity.is_on is None

    async def test_device_info(self, aioclient_mock):
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO)
        entity = (await self.async_entities(aioclient_mock))[0]
        assert entity.device_info["name"] == "My dimmer"
        assert entity.device_info["mac"] == "1afe34e750b8"
        assert entity.device_info["manufacturer"] == "BleBox"
        assert entity.device_info["model"] == "dimmerBox"
        assert entity.device_info["sw_version"] == "0.247"

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
        assert entity.brightness == 255

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

    DEVICE_EXTENDED_INFO_PATH = "/api/rgbw/extended/state"
    DEV_INFO_PATH = "api/rgbw/state"
    DEVICE_INFO = json.loads(
        """
    {
        "device": {
            "deviceName": "My wLightBoxS",
            "type": "wLightBox",
            "product":"wLightBoxS",
            "fv": "0.924",
            "hv": "0.1",
            "universe": 0,
            "id": "1afe34e750b8",
            "apiLevel": 20200229,
            "ip": "192.168.9.13",
            "availableFv": null
        }
    }
    """
    )

    DEVICE_INFO2 = {
        "device": {
            "deviceName": "My wLightBoxS",
            "type": "wLightBox",
            "product": "wLightBoxS",
            "hv": "s_0.1",
            "fv": "0.1022",
            "universe": 0,
            "apiLevel": "20200229",
            "id": "ce50e32d2707",
            "ip": "192.168.1.25",
            "availableFv": None,
        }
    }

    DEVICE_EXTENDED_INFO = {
        "rgbw": {
            "desiredColor": "f5",
            "currentColor": "f5",
            "lastOnColor": "f5",
            "durationsMs": {"colorFade": 1000, "effectFade": 1000, "effectStep": 1000},
            "effectID": 0,
            "colorMode": 3,
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }

    def patch_version(apiLevel):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{ "device": {{ "apiLevel": {apiLevel} }} }}
        """

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(future_date()))
    DEVICE_INFO_LATEST = jmerge(
        DEVICE_INFO, patch_version(get_latest_api_level("wLightBoxS"))
    )
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
        "rgbw": {
            "desiredColor": "e3",
            "currentColor": "df",
            "fadeSpeed": 255,
            "effectID": 0
        }
    }
    """
    )

    STATE_ON = json.loads(
        """
        {
            "rgbw": {
                "desiredColor": "ab",
                "currentColor": "cd",
                "fadeSpeed": 255,
                "effectID": 0,
                "colorMode": 3
            }
        }
    """
    )

    STATE_FULL_ON = json.loads(
        """
        {
            "rgbw": {
                "desiredColor": "ff",
                "currentColor": "ce",
                "fadeSpeed": 255,
                "effectID": 0
            }
        }
    """
    )

    STATE_OFF = json.loads(
        """
        {
            "rgbw": {
                "desiredColor": "00",
                "currentColor": "00",
                "fadeSpeed": 255,
                "effectID": 0
            }
        }
    """
    )

    STATE_DEFAULT = STATE_ON

    async def test_init(self, aioclient_mock):
        """Test cover default state."""
        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        assert entity.name == "My wLightBoxS (wLightBoxS#brightness_mono1)"
        assert entity.unique_id == "BleBox-wLightBoxS-1afe34e750b8-brightness_mono1"
        print(entity.color_mode)
        # assert entity.color_mode & SUPPORT_BRIGHTNESS this assertion needs to be refactored, after extended state will be mockable
        assert entity.brightness is None

        assert entity.is_on is None

    async def test_device_info(self, aioclient_mock):
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO)
        entity = (await self.async_entities(aioclient_mock))[0]
        assert entity.device_info["name"] == "My wLightBoxS"
        assert entity.device_info["mac"] == "1afe34e750b8"
        assert entity.device_info["manufacturer"] == "BleBox"
        assert entity.device_info["model"] == "wLightBoxS"
        assert entity.device_info["sw_version"] == "0.924"

    async def test_device_info2(self, aioclient_mock):
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO2)
        entity = (await self.async_entities(aioclient_mock))[0]
        assert entity.device_info["name"] == "My wLightBoxS"
        assert entity.device_info["mac"] == "ce50e32d2707"
        assert entity.device_info["manufacturer"] == "BleBox"
        assert entity.device_info["model"] == "wLightBoxS"
        assert entity.device_info["sw_version"] == "0.1022"

    async def test_update(self, aioclient_mock):
        """Test light updating."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)
        print("TU:", entity.color_mode)
        assert entity.brightness == 0xAB
        assert entity.is_on is True

    async def allow_set_brightness(self, code, aioclient_mock, value, response):
        """Set up mock for HTTP POST simulating color change."""
        print("allow_set_brightness", response)
        raw = "{:02x}".format(value)
        await self.allow_post(
            code,
            aioclient_mock,
            "/api/rgbw/set",
            json.dumps(
                {"rgbw": {"desiredColor": raw + "------"}}
            ),  # simulating mask for color mod 3
            response,
        )

    async def test_on(self, aioclient_mock):
        """Test light on."""
        entity = await self.updated(aioclient_mock, self.STATE_OFF)
        print("Ent: ", entity)
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

    DEVICE_EXTENDED_INFO_PATH = "/api/rgbw/extended/state"
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
    DEVICE_EXTENDED_INFO = {
        "rgbw": {
            "colorMode": 4,
            "effectID": 0,
            "desiredColor": "fa00203A",
            "currentColor": "ff00302F",
            "lastOnColor": "f1e2d3e4",
            "durationsMs": {"colorFade": 1000, "effectFade": 1500, "effectStep": 2000},
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }
    DEVICE_EXTENDED_INFO_COLORMODE_1 = {
        "rgbw": {
            "colorMode": 1,
            "effectID": 0,
            "desiredColor": "fa",
            "currentColor": "ff",
            "lastOnColor": "ff",
            "durationsMs": {"colorFade": 1000, "effectFade": 1500, "effectStep": 2000},
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }
    DEVICE_EXTENDED_INFO_COLORMODE_2 = {
        "rgbw": {
            "colorMode": 2,
            "effectID": 0,
            "desiredColor": "fa00203A",
            "currentColor": "ff00302F",
            "lastOnColor": "f1e2d3e4",
            "durationsMs": {"colorFade": 1000, "effectFade": 1500, "effectStep": 2000},
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }
    DEVICE_EXTENDED_INFO_COLORMODE_3 = {
        "rgbw": {
            "colorMode": 3,
            "effectID": 0,
            "desiredColor": "fa00203A",
            "currentColor": "ff00302F",
            "lastOnColor": "f1e2d3e4",
            "durationsMs": {"colorFade": 1000, "effectFade": 1500, "effectStep": 2000},
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }
    DEVICE_EXTENDED_INFO_COLORMODE_4 = {
        "rgbw": {
            "colorMode": 4,
            "effectID": 0,
            "desiredColor": "fa00203A",
            "currentColor": "ff00302F",
            "lastOnColor": "f1e2d3e4",
            "durationsMs": {"colorFade": 1000, "effectFade": 1500, "effectStep": 2000},
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }
    DEVICE_EXTENDED_INFO_COLORMODE_5 = {
        "rgbw": {
            "colorMode": 5,
            "effectID": 0,
            "desiredColor": "fa00203A",
            "currentColor": "ff00302F",
            "lastOnColor": "f1e2d3e4",
            "durationsMs": {"colorFade": 1000, "effectFade": 1500, "effectStep": 2000},
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }

    DEVICE_EXTENDED_INFO_COLORMODE_6 = {
        "rgbw": {
            "colorMode": 6,
            "effectID": 0,
            "desiredColor": "fa00203A",
            "currentColor": "ff00302F",
            "lastOnColor": "f1e2d3e4",
            "durationsMs": {"colorFade": 1000, "effectFade": 1500, "effectStep": 2000},
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }
    DEVICE_EXTENDED_INFO_COLORMODE_7 = {
        "rgbw": {
            "colorMode": 7,
            "effectID": 0,
            "desiredColor": "fcfffcff00",
            "currentColor": "fcfffcff00",
            "lastOnColor": "fcfffcff00",
            "durationsMs": {"colorFade": 1000, "effectFade": 1000, "effectStep": 1000},
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }

    def patch_version(apiLevel):
        """Generate a patch for a JSON state fixture."""
        return f"""
        {{ "device": {{ "apiLevel": {apiLevel} }} }}
        """

    DEVICE_INFO_FUTURE = jmerge(DEVICE_INFO, patch_version(future_date()))
    DEVICE_INFO_LATEST = jmerge(
        DEVICE_INFO, patch_version(get_latest_api_level("wLightBox"))
    )
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
        "colorMode": 4,
        "effectID": 0,
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

        assert entity.name == "My light 1 (wLightBox#color_RGBorW)"
        assert entity.unique_id == "BleBox-wLightBox-1afe34e750b8-color_RGBorW"
        # In current state of master branch white_value is not property of BleBoxLightEntity, fake test... dissapointing
        # assert entity.supported_features & SUPPORT_WHITE_VALUE
        # assert entity.white_value is None

        # assert entity.supported_features & SUPPORT_COLOR
        # assert entity.hs_color is None
        # assert entity.white_value is None

        # assert entity.supported_features & SUPPORT_BRIGHTNESS
        # assert entity.brightness == 123
        assert entity.is_on is None

    async def test_device_info(self, aioclient_mock):
        await self.allow_get_info(aioclient_mock, self.DEVICE_INFO)
        entity = (await self.async_entities(aioclient_mock))[0]
        assert entity.device_info["name"] == "My light 1"
        assert entity.device_info["mac"] == "1afe34e750b8"
        assert entity.device_info["manufacturer"] == "BleBox"
        assert entity.device_info["model"] == "wLightBox"
        assert entity.device_info["sw_version"] == "0.993"

    async def test_update(self, aioclient_mock):
        """Test light updating."""

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)
        assert entity.brightness == 250
        # assert entity.hs_color == (352.32, 100.0)
        # assert entity.white_value == 0x3A
        assert entity.is_on is True  # state already available

    async def allow_set_color(self, code, aioclient_mock, value, response):
        """Set up mock for HTTP POST simulating color change."""
        print("allow_set_color", response)
        await self.allow_post(
            code,
            aioclient_mock,
            "/api/rgbw/set",
            '{"rgbw":{"desiredColor": "' + str(value) + '"}}',
            response,
        )

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
        # assert entity.white_value == 0xE4
        assert entity.rgbw_color == tuple(
            [int(i, 16) for i in ["f1", "e2", "d3", "e4"]]
        )

    async def test_off(self, aioclient_mock):
        """Test light off."""
        entity = await self.updated(aioclient_mock, self.STATE_ON)
        assert entity.is_on is True

        async def action():
            await entity.async_turn_off()

        await self.allow_set_color(action, aioclient_mock, "00000000", self.STATE_OFF)

        assert entity.is_on is False
        # assert entity.white_value == 0x00

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
        with pytest.raises(UnsupportedBoxVersion):
            await self.async_entities(aioclient_mock)

    """
        1. ustawic setup mocka do inicjalizacji obiektu
        2. dostep do encji
        3. asercje
    """

    async def test_colormode_5_brightness(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_5
        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 5
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert "_cct" in entity.name
        assert entity.brightness == 250

    async def test_colormode_6_brightness(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_6
        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 6
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT, 1)

        assert "_cct2" in entity.name
        assert entity.brightness

    async def test_many_from_config_check_empty(self, aioclient_mock):
        pass

    async def test_effect_list_return_list(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_5
        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 5
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert entity.effect_list

    async def test_color_temp_for_colomode_6(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_6
        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 6
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert "_cct1" in entity.name
        assert entity.color_temp

    async def test_color_temp_for_colomode_rgbww(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_7
        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 7
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        assert "_RGBCCT" in entity.name
        assert entity.color_temp
        assert entity.brightness

    async def test_normalise_element_colormode_rgb(self, aioclient_mock):
        # testing sensible on value which is used only while async_turn_on executed

        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_2
        self.DEVICE_EXTENDED_INFO = jmerge(
            self.DEVICE_EXTENDED_INFO, self.patch_state("fafafa", "fafafa")
        )
        self.STATE_DEFAULT["rgbw"]["colorMode"] = 2

        self.STATE_DEFAULT = jmerge(
            self.STATE_DEFAULT, self.patch_state("fafafa", "fafafa")
        )

        await self.allow_get_info(aioclient_mock)
        print("INTEST:\n", self.DEVICE_EXTENDED_INFO, "\nEntity:\n")
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        async def turn_on():
            await entity.async_turn_on(rgb_color=(255, 0, 140))

        self.STATE_ON = jmerge(self.STATE_ON, self.patch_state("fafafa", "fafafa"))
        await self.allow_set_color(turn_on, aioclient_mock, "fa0089", self.STATE_ON)

        assert max(entity.rgbw_color) == 250

    async def test_normalise_when_max_is_zero_rgb(self, aioclient_mock):
        # testing sensible on value which is used only while async_turn_on executed

        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_2
        self.DEVICE_EXTENDED_INFO = jmerge(
            self.DEVICE_EXTENDED_INFO, self.patch_state("030303", "030303")
        )
        self.STATE_DEFAULT["rgbw"]["colorMode"] = 2

        self.STATE_DEFAULT = jmerge(
            self.STATE_DEFAULT, self.patch_state("030303", "030303")
        )

        await self.allow_get_info(aioclient_mock)
        print("INTEST:\n", self.DEVICE_EXTENDED_INFO, "\nEntity:\n")
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        async def turn_on():
            await entity.async_turn_on(rgb_color=(255, 10, 255))

        self.STATE_ON = jmerge(self.STATE_ON, self.patch_state("000000", "000000"))
        await self.allow_set_color(turn_on, aioclient_mock, "030003", self.STATE_ON)

        assert max(entity.rgb_color) == 255

    async def test_sensible_on_value_for_color_mode_1(self, aioclient_mock):

        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_1
        self.DEVICE_EXTENDED_INFO = jmerge(
            self.DEVICE_EXTENDED_INFO, self.patch_state("00000000", "00000000")
        )
        self.STATE_DEFAULT["rgbw"]["colorMode"] = 1

        self.STATE_DEFAULT = jmerge(
            self.STATE_DEFAULT, self.patch_state("00000000", "00000000")
        )

        await self.allow_get_info(aioclient_mock)

        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        async def turn_on():
            await entity.async_turn_on()

        self.STATE_ON = jmerge(self.STATE_ON, self.patch_state("ffffffff", "ffffffff"))
        await self.allow_set_color(turn_on, aioclient_mock, "ffffffff", self.STATE_ON)

        assert entity.rgbw_color == (255, 255, 255, 255)

    async def test_sensible_on_value_for_color_mode_5(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_5
        self.DEVICE_EXTENDED_INFO = jmerge(
            self.DEVICE_EXTENDED_INFO, self.patch_state("00000000", "00000000")
        )
        self.STATE_DEFAULT["rgbw"]["colorMode"] = 5

        self.STATE_DEFAULT = jmerge(
            self.STATE_DEFAULT, self.patch_state("00000000", "00000000")
        )

        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 5
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        print("INTEST:\n", entity.name, "\nEntity:\n")

        async def turn_on():
            await entity.async_turn_on()

        self.STATE_ON = jmerge(self.STATE_ON, self.patch_state("ffffffff", "ffffffff"))
        await self.allow_set_color(turn_on, aioclient_mock, "ffff------", self.STATE_ON)

        assert entity.color_temp == 128

    async def test_turn_on_color_temp_full_warm_for_color_mode_5(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_5
        self.STATE_DEFAULT["rgbw"]["colorMode"] = 5

        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 5
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        print("INTEST:\n", entity.name, "\nEntity:\n")

        async def turn_on():
            await entity.async_turn_on(color_temp=1)

        self.STATE_ON = jmerge(self.STATE_ON, self.patch_state("02ffffff", "02ffffff"))

        await self.allow_set_color(turn_on, aioclient_mock, "02fa------", self.STATE_ON)

        assert entity.color_temp == 1

    async def test_turn_on_color_temp_full_cold_for_color_mode_5(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_5
        self.STATE_DEFAULT["rgbw"]["colorMode"] = 5

        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 5
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        async def turn_on():
            await entity.async_turn_on(color_temp=255)

        self.STATE_ON = jmerge(self.STATE_ON, self.patch_state("fa00ffff", "fa02ffff"))

        await self.allow_set_color(turn_on, aioclient_mock, "fa00------", self.STATE_ON)

        assert entity.color_temp == 255

    async def test_sensible_on_value_for_color_mode_6(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_6
        self.STATE_DEFAULT["rgbw"]["colorMode"] = 6

        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 6
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        async def turn_on():
            await entity.async_turn_on(color_temp=255)

        self.STATE_ON = jmerge(self.STATE_ON, self.patch_state("fa00ffff", "fa02ffff"))

        await self.allow_set_color(turn_on, aioclient_mock, "fa00------", self.STATE_ON)

        assert entity.color_temp == 255

    async def test_sensible_on_value_for_color_mode_7(self, aioclient_mock):
        self.DEVICE_EXTENDED_INFO = self.DEVICE_EXTENDED_INFO_COLORMODE_7
        self.STATE_DEFAULT["rgbw"]["colorMode"] = 7
        self.STATE_DEFAULT = jmerge(
            self.STATE_DEFAULT, self.patch_state("fcfffcff00", "fcfffcff00")
        )
        await self.allow_get_info(aioclient_mock)
        self.STATE_DEFAULT["colorMode"] = 7
        entity = await self.updated(aioclient_mock, self.STATE_DEFAULT)

        async def turn_on():
            await entity.async_turn_on(rgbww_color=(0, 0, 0, 120, 214))

        self.STATE_ON = jmerge(
            self.STATE_ON, self.patch_state("000000d678", "000000d678")
        )

        await self.allow_set_color(turn_on, aioclient_mock, "000000d678", self.STATE_ON)

        assert entity.rgbww_color == (0, 0, 0, 120, 214)


def test_unit_light_evaluate_brightness_from_rgb():
    tested_ob = Light.evaluate_brightness_from_rgb(iterable=(140, 230))
    assert tested_ob == 230
