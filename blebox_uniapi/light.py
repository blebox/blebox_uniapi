import bisect
from datetime import timedelta
from .feature import Feature

from .error import BadOnValueError, BadFadeSpeedValueError


class Light(Feature):
    # TODO: better defaults?

    FADE_SPEED = [0, 6, 12, 12, 21, 24, 39, 48, 63, 75, 93, 105, 120, 156, 183, 222, 258, 309, 342,
                  384, 441, 513, 615, 684, 768, 855, 1026, 1197, 1280, 1368, 1435, 1536, 1640, 1710,
                  1792, 1845, 2048, 2304, 2560, 2736, 3072, 3584, 4096, 5120, 6144, 7168, 8192, 9216,
                  10240, 11264, 12288, 13312, 14336, 15360, 16384, 18432, 20480, 22528, 24576, 26624,
                  28672, 30720, 32768, 34816, 36864, 38912, 40960, 43008, 45056, 47104, 49152, 51200,
                  53248, 55296, 57344, 59392, 61440, 63488, 65536, 67584, 69632, 71680, 73728, 75776,
                  77824, 79872, 81920, 84992, 88064, 91136, 93184, 94208, 96256, 97280, 99328, 100352,
                  102400, 105472, 105472, 108544, 108544, 111616, 111616, 114688, 115712, 117760, 118784,
                  120832, 121856, 122880, 123904, 125952, 125952, 128000, 132096, 136192, 139264, 142336,
                  144384, 146432, 148480, 151552, 155648, 160768, 164864, 168960, 169984, 174080, 175104,
                  178176, 184320, 189440, 195584, 199680, 200704, 205824, 206848, 211968, 218112, 224256,
                  230400, 237568, 237568, 244736, 244736, 251904, 259072, 266240, 273408, 274432, 281600,
                  282624, 290816, 299008, 308224, 316416, 318464, 325632, 327680, 336896, 346112, 356352,
                  366592, 368640, 376832, 379904, 390144, 401408, 412672, 416768, 424960, 429056, 441344,
                  453632, 466944, 472064, 480256, 485376, 499712, 514048, 528384, 535552, 542720, 550912,
                  566272, 582656, 599040, 608256, 616448, 625664, 643072, 661504, 672768, 679936, 691200,
                  711680, 731136, 744448, 752640, 765952, 787456, 809984, 825344, 832512, 860160, 873472,
                  898048, 916480, 923648, 942080, 969728, 996352, 1018880, 1047552, 1077248, 1107968,
                  1133568, 1138688, 1165312, 1198080, 1231872, 1262592, 1266688, 1297408, 1334272,
                  1368064, 1372160, 1406976, 1445888, 1483776, 1486848, 1525760, 1568768, 1611776,
                  1613824, 1656832, 1703936, 1751040, 1752064, 1800192, 1851392, 1903616, 1904640,
                  1953792, 2013184, 2019328, 2070528, 2076672, 2135040, 2195456, 2320384, 2453504,
                  2593792, 2710528, 3073024, 3614720]

    CONFIG = {
        "wLightBox": {
            "default": "FFFFFFFF",
            "off": "00000000",
            "brightness?": False,
            "fade_speed?": False,
            "white?": True,
            "color?": True,
            "to_value": lambda int_value: int_value,
            "validator": lambda product, alias, raw: product.expect_rgbw(alias, raw),
        },
        "wLightBoxS": {
            "default": "FF",
            "off": "00",
            "brightness?": True,
            "fade_speed?": True,
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: "{:02x}".format(int_value),
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        },
        "dimmerBox": {
            "default": 0xFF,
            "off": 0x0,
            "brightness?": True,
            "fade_speed?": True,
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: int_value,
            "validator": lambda product, alias, raw: product.expect_int(
                alias, raw, 255, 0
            ),
        },
    }

    def __init__(self, product, alias, methods):
        super().__init__(product, alias, methods)

        config = self.CONFIG[product.type]
        self._off_value = config["off"]
        self._last_on_state = self._default_on_value = config["default"]

    @property
    def supports_brightness(self):
        return self.CONFIG[self._product.type]["brightness?"]

    @property
    def brightness(self):
        return self._desired if self.supports_brightness else None

    def apply_brightness(self, value, brightness):
        if brightness is None:
            return value

        if not isinstance(brightness, int):
            raise BadOnValueError(
                f"adjust_brightness called with bad parameter ({brightness} is {type(value)} instead of int)"
            )

        if brightness > 255:
            raise BadOnValueError(
                f"adjust_brightness called with bad parameter ({brightness} is greater than 255)"
            )

        if not self.supports_brightness:
            return value

        method = self.CONFIG[self._product.type]["to_value"]

        return method(brightness)  # ok since not implemented for rgbw

    @property
    def supports_fade_speed(self):
        return self.CONFIG[self._product.type]["fade_speed?"]

    def apply_fade_speed(self, fade_speed):
        if not isinstance(fade_speed, timedelta):
            raise BadFadeSpeedValueError(
                f"apply_fade_speed called with bad parameter ({fade_speed} is {type(fade_speed)} instead of timedelta)")

        if timedelta() > fade_speed > timedelta(hours=1):
            raise BadFadeSpeedValueError(
                f"apply_fade_speed called with bad parameter ({fade_speed} is not within range of 0..1h)")

        fade_speed = int(fade_speed / timedelta(milliseconds=1))
        return 255 - bisect.bisect_left(self.FADE_SPEED, fade_speed)

    @property
    def supports_white(self):
        return self.CONFIG[self._product.type]["white?"]

    @property
    def white_value(self):
        return self._white_value

    def apply_white(self, value, white):
        if white is None:
            return value

        if not self.supports_white:
            return value

        rgbhex = value[0:6]
        white_raw = "{:02x}".format(white)
        return f"{rgbhex}{white_raw}"

    @property
    def supports_color(self):
        return self.CONFIG[self._product.type]["color?"]

    def apply_color(self, value, rgb_hex):
        if rgb_hex is None:
            return value

        if not self.supports_color:
            return value

        white_hex = value[6:8]
        return f"{rgb_hex}{white_hex}"

    @property
    def is_on(self):
        return self._is_on

    def after_update(self):
        alias = self._alias
        product = self._product
        if product.last_data is None:
            self._desired_raw = None
            self._desired = None
            self._is_on = None
            if product.type == "wLightBox":
                self._white_value = None
            return

        raw = self.raw_value("desired")

        self._desired_raw = raw

        self._desired = self.CONFIG[self._product.type]["validator"](
            product, alias, raw
        )

        if product.type == "wLightBox":
            self._white_value = int(raw[6:8], 16)

        if raw == self._off_value:
            if product.type == "wLightBox":
                raw = product.expect_rgbw(alias, self.raw_value("last_color"))
            else:
                raw = self._default_on_value

        if raw in (self._off_value, None):
            raise BadOnValueError(raw)

        # TODO: store as custom value permanently (exposed by API consumer)
        self._last_on_state = raw
        self._is_on = self._desired_raw != self._off_value

    @property
    def sensible_on_value(self):
        return self._last_on_state

    @property
    def rgbw_hex(self):
        return self._desired

    async def async_on(self, value, fade_speed=None):
        if not isinstance(value, type(self._off_value)):
            raise BadOnValueError(
                f"turn_on called with bad parameter ({value} is {type(value)}, compared to {self._off_value} which is {type(self._off_value)})"
            )

        if value == self._off_value:
            raise BadOnValueError(f"turn_on called with invalid value ({value})")

        if not self.supports_fade_speed:
            await self.async_api_command("set", value)
        else:
            self.validate_fade_speed(fade_speed)
            await self.async_api_command("set", value, fade_speed)

    async def async_off(self, fade_speed=None):
        if not self.supports_fade_speed:
            await self.async_api_command("set", self._off_value)
        else:
            self.validate_fade_speed(fade_speed)
            await self.async_api_command("set", self._off_value, fade_speed)

    def validate_fade_speed(self, fade_speed):
        if fade_speed is None:
            return
        if not isinstance(fade_speed, int):
            raise BadFadeSpeedValueError(f"turn_on called with invalid fade_speed value type ({type(fade_speed)})")
        if 0 > fade_speed > 255:
            raise BadFadeSpeedValueError(f"turn_on called with fade_speed value out of range ({fade_speed})")
