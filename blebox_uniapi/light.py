from enum import IntEnum
from .feature import Feature
from typing import TYPE_CHECKING, Optional, Dict, Any, Union, Sequence

if TYPE_CHECKING:
    from .box import Box

# V3 onwards used while device is operating on 5 channels, refactor if new versions occurs
ctx2_v3 = {"cct1": lambda x: f"{x}------", "cct2": lambda x: f"----{x}--"}
ctx2 = {"cct1": lambda x: f"{x}----", "cct2": lambda x: f"----{x}"}

mono = {
    "mono1": lambda x: f"{x}------",
    "mono2": lambda x: f"--{x}----",
    "mono3": lambda x: f"----{x}--",
    "mono4": lambda x: f"------{x}",
}


class BleboxColorMode(IntEnum):
    RGBW = 1  # RGB color-space with color brightness, white brightness
    RGB = 2  # RGB color-space with color brightness
    MONO = 3
    RGBorW = 4  # RGBW entity, where white color is prioritised
    CT = 5  # color-temperature, brightness, effect
    CTx2 = 6  # color-temperature, brightness, effect, two instances
    RGBWW = 7  # RGB with two color-temperature sliders(warm, cold)

    @classmethod
    def invert(cls):
        return {item.value: item.name for item in cls}


BLEBOX_COLOR_MODES = BleboxColorMode.invert()


class Light(Feature):
    # TODO: better defaults?
    CURRENT_CONF = dict()
    CONFIG = {
        "wLightBox": {
            "default": "FFFFFFFF",
            "off": "00000000",
            "white?": True,
            "color?": True,
            "to_value": lambda int_value: f"{int_value:02x}",
            "validator": lambda product, alias, raw: product.expect_rgbw(alias, raw),
        },
        "wLightBoxS": {
            "default": "FF",
            "off": "00",
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: f"{int_value:02x}",
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        },
        "dimmerBox": {
            "default": 0xFF,
            "off": 0x0,
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: int_value,
            "validator": lambda product, alias, raw: product.expect_int(
                alias, raw, 255, 0
            ),
        },
    }

    COLOR_MODE_CONFIG = {
        "CT": {
            "default": "FFFFFFFF",
            "off": "0000",
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: f"{int_value:02x}",
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        },
        "CTx2": {
            "default": "FFFFFFFF",
            "off": "0000",
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: f"{int_value:02x}",
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        },
        "RGBWW": {
            "default": "FFFFFFFFFF",
            "off": "0000000000",
            "white?": True,
            "color?": True,
            "to_value": lambda int_value: f"{int_value:02x}",
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        },
    }

    def __init__(
        self,
        product: "Box",
        alias: str,
        methods: dict,
        extended_state: Optional[Dict],
        mask: Any,
        desired_color,
        color_mode,
        effect_list,
        current_effect,
    ) -> None:
        super().__init__(product, alias, methods)
        config = self.CONFIG[product.type]
        self.mask = mask
        self.desired_color = desired_color
        self._color_mode = color_mode
        self._effect_list = effect_list
        if self._effect_list is not None:
            self._effect = current_effect

        if extended_state not in [None, {}]:
            self.extended_state = extended_state
            self.device_colorMode = color_mode
            if self.device_colorMode in [6, 7]:
                config = self.COLOR_MODE_CONFIG[
                    BLEBOX_COLOR_MODES[self.device_colorMode]
                ]
        else:
            if product.type == "dimmerBox":
                self.device_colorMode = BleboxColorMode.MONO
        self.CURRENT_CONF = config

        self._off_value = self.evaluate_off_value(config, desired_color)
        self._last_on_state = self._default_on_value = config["default"]

    @classmethod
    def many_from_config(
        cls, product, box_type_config, extended_state
    ) -> list["Light"]:

        if isinstance(extended_state, dict) and extended_state is not None:
            desired_color = extended_state.get("rgbw", {}).get("desiredColor")
            color_mode = extended_state.get("rgbw", {}).get("colorMode")
            current_effect = extended_state.get("rgbw", {}).get("effectID")
            effect_list = extended_state.get("rgbw", {}).get("effectsNames")
        else:
            desired_color = None
            color_mode = None
            current_effect = None
            effect_list = None
        alias, methods = box_type_config[0]
        const_kwargs = dict(
            methods=methods,
            extended_state=extended_state,
            desired_color=desired_color,
            color_mode=color_mode,
            current_effect=current_effect,
            effect_list=effect_list,
        )

        if extended_state is not None and color_mode is not None:
            if BleboxColorMode(color_mode).name == "RGBW":
                if len(desired_color) == 10:
                    mask = lambda x: f"{x}--"
                else:
                    mask = None
                return [cls(product, alias=alias + "_RGBW", mask=mask, **const_kwargs)]

            if BleboxColorMode(color_mode).name == "RGB":
                return [cls(product, alias=alias + "_RGB", mask=None, **const_kwargs)]

            if BleboxColorMode(color_mode).name == "MONO":
                if len(desired_color) % 2 == 0:
                    object_list = []
                    mono_item = list(mono.items())
                    for i in range(0, int(len(desired_color) / 2)):
                        indicator, mask = mono_item[i]
                        object_list.append(
                            cls(
                                product,
                                alias=alias + "_" + indicator,
                                mask=mask,
                                **const_kwargs,
                            )
                        )
                    return object_list

            if BleboxColorMode(color_mode).name == "RGBorW":
                return [
                    cls(product, alias=alias + "_RGBorW", mask=None, **const_kwargs)
                ]

            if BleboxColorMode(color_mode).name == "CT":
                mask = ctx2["cct1"]
                if len(desired_color) > 8:
                    mask = ctx2_v3["cct1"]
                return [cls(product, alias=alias + "_cct", mask=mask, **const_kwargs)]

            if BleboxColorMode(color_mode).name == "CTx2":
                object_list = []
                ct = ctx2
                if len(desired_color) > 8:
                    ct = ctx2_v3
                for indicator, mask in ct.items():
                    object_list.append(
                        cls(
                            product,
                            alias=alias + "_" + indicator,
                            mask=mask,
                            **const_kwargs,
                        )
                    )
                return object_list

            if BleboxColorMode(color_mode).name == "RGBWW":
                return [
                    cls(product, alias=alias + "_RGBCCT", mask=None, **const_kwargs)
                ]

        if len(box_type_config) > 0:
            del const_kwargs["methods"]
            if "Brightness" in box_type_config[0][1].get("desired"):
                const_kwargs["color_mode"] = BleboxColorMode.MONO
            return [
                cls(product, *args, mask=None, **const_kwargs)
                for args in box_type_config
            ]
        else:
            return []

    @property
    def brightness(self) -> Optional[int]:
        if self.color_mode in [6, 5]:
            _, bgt = self.color_temp_brightness_int_from_hex(self._desired)
            return bgt
        elif self.color_mode is not None and (
            rgb_list := self.rgb_hex_to_rgb_list(self.rgb_hex)
        ):
            return self.evaluate_brightness_from_rgb(rgb_list)
        else:
            return None

    @property
    def effect_list(self):
        if isinstance(self._effect_list, dict):
            return list(self._effect_list.values())
        else:
            return []

    @property
    def color_temp(self):
        ct, _ = self.color_temp_brightness_int_from_hex(self._desired)
        return ct

    @staticmethod
    def evaluate_brightness_from_rgb(iterable: Sequence[int]) -> int:
        "return brightness from 0 to 255 evaluated basing rgb"
        if max(iterable) > 255:
            raise ValueError(
                f"evaluate_brightness_from_rgb values out of range, max is {max(iterable)}."
            )
        elif min(iterable) < 0:
            raise ValueError(
                f"evaluate_brightness_from_rgb values out of range, min is {min(iterable)}."
            )
        return int(max(iterable))

    def apply_brightness(self, value: int, brightness: int) -> Any:
        """Return list of values with applied brightness."""
        if not isinstance(brightness, int):
            raise ValueError(
                f"adjust_brightness called with bad parameter ({brightness} is {type(brightness)} instead of int)"
            )

        if brightness > 255:
            raise ValueError(
                f"adjust_brightness called with bad parameter ({brightness} is greater than 255)"
            )

        if self.product.type == "dimmerBox" or self.color_mode == BleboxColorMode.MONO:
            return [brightness]
        if brightness == 0:
            return [value]

        res = list(map(lambda x: round(x * (brightness / 255)), value))
        return res

    def evaluate_off_value(self, config: dict, raw_hex: str) -> str:
        """
        Return hex representing off state value without mask formatting for necessary channels if mask is applied.
        If no mask applied than return default from config

        :param config:
        :param raw_hex:
        :return: str
        """
        if self.mask:
            if len(raw_hex) < len(self.mask("x").replace("x", "")):
                return "0" * len(raw_hex)
            else:
                return "0" * (len(raw_hex) - len(self.mask("x").replace("x", "")))
        elif raw_hex is not None:
            if len(raw_hex) < len(config["off"]):
                return config["off"][: len(raw_hex)]
        return config["off"]

    @property
    def supports_white(self) -> Any:
        return self.CURRENT_CONF["white?"]

    @property
    def white_value(self) -> Optional[int]:
        return self._white_value

    def apply_white(self, value: str, white: int) -> Union[int, str]:
        if white is None:
            return value

        if not self.supports_white:
            return value

        rgbhex = value[0:6]
        white_raw = f"{white:02x}"
        return f"{rgbhex}{white_raw}"

    @property
    def supports_color(self) -> Any:
        return self.CURRENT_CONF["color?"]

    @property
    def color_mode(self) -> int:
        return self._color_mode

    def apply_color(self, value: str, rgb_hex: str) -> Union[int, str]:
        if rgb_hex is None:
            return value

        if not self.supports_color:
            return value

        white_hex = value[6:8]
        return f"{rgb_hex}{white_hex}"

    def return_color_temp_with_brightness(
        self, value, brightness: Any
    ) -> Optional[str]:
        """Method returns value which will be send to"""
        if value < 128:
            warm = min(255, value * 2)
            cold = 255
        else:
            warm = 255
            cold = max(0, min(255, (255 - value) * 2))
        cold = cold * brightness / 255
        warm = warm * brightness / 255
        cold = f"{int(round(cold)):02x}"
        warm = f"{int(round(warm)):02x}"

        return self.rgb_hex_to_rgb_list(warm + cold)

    def value_for_selected_channels_from_given_val(self, value: str):
        if self.color_mode in [BleboxColorMode.CT, BleboxColorMode.CTx2]:
            lambda_result = self.mask("xxxx")
        elif self.color_mode == BleboxColorMode.MONO:
            lambda_result = self.mask("xx")
        elif self.color_mode == BleboxColorMode.RGB:
            lambda_result = self.mask("xxxxxx")
        elif (
            self.color_mode == BleboxColorMode.RGBW
            or self.color_mode == BleboxColorMode.RGBorW
        ):
            lambda_result = self.mask("xxxxxxxx")
        first_index = lambda_result.index("x")
        last_index = lambda_result.rindex("x")
        return value[first_index : last_index + 1]

    @staticmethod
    def color_temp_brightness_int_from_hex(val) -> (int, int):
        """Assuming that hex is 2channels, 4characters. Return values for front end"""

        cold = int(val[2:], 16)
        warm = int(val[0:2], 16)

        if cold > warm:
            if warm == 0:
                return 0, cold
            else:
                return round(int((128 * (warm * 255 / cold) / 255)), 2), cold
        if cold < warm:
            if cold == 0:
                return 255, warm
            else:
                return round(int(255 - 128 * (cold * (255 / warm) / 255)), 2), warm
        else:
            return 128, max(cold, warm)

    @staticmethod
    def normalise_elements_of_rgb(elements):
        max_val = max(elements)
        min_val = min(elements)
        if 0 > max_val or max_val > 255:
            raise ValueError(f"Max value in normalisation was outside range {max_val}.")
        elif min_val < 0:
            raise ValueError(f"Min value in normalisation was outside range {min_val}.")
        elif max_val == 0:
            return [255] * len(elements)
        return list(map(lambda x: round(x * 255 / max_val), elements))

    @property
    def is_on(self) -> Optional[bool]:
        return self._is_on

    @property
    def effect(self) -> Optional[str]:
        if isinstance(self._effect_list, dict):
            return self._effect_list.get(str(self._effect))
        return self._effect

    def after_update(self) -> None:
        alias = self._alias
        product = self._product

        if product.last_data is None:
            self._desired_raw = None
            self._desired = None
            self._is_on = None
            self._effect = None
            if self.mask is None:
                self._white_value = None
            return

        self._effect = self.raw_value("currentEffect")
        raw = self._return_desired_value(alias, product)
        self._set_last_on_value(alias, product, raw)
        self._set_is_on()

    def _set_last_on_value(self, alias, product, raw):
        if raw == self._off_value:
            if (
                product.type == "wLightBox"
            ):  # jezeli urzadzenie typu wLightBox ma wyciagnac last_color
                raw = product.expect_rgbw(alias, self.raw_value("last_color"))
                if self.mask is not None:
                    raw = self.value_for_selected_channels_from_given_val(raw)
                    if raw == self._off_value:
                        raw = self.value_for_selected_channels_from_given_val(
                            "ffffffffff"
                        )
                else:
                    if raw == self._off_value:
                        raw = "f" * len(raw)
            else:
                raw = self._default_on_value

        if raw in (self._off_value, None):
            raise ValueError(raw)
        # TODO: store as custom value permanently (exposed by API consumer)
        self._last_on_state = raw

    def _set_is_on(self):
        self._is_on = (self._off_value != self._desired) or (
            self._effect != 0 and self._effect is not None
        )
        if isinstance(self._desired, str):
            if int(self._desired, 16) == 0:
                self._is_on = False

    def _return_desired_value(self, alias, product) -> str:
        """
        Return value representing desired device state, set desired fields
        :param alias:
        :param product:
        :return desired value including mask:
        """

        response_desired_val = self.raw_value("desired")
        if self.mask is not None:
            raw = self.value_for_selected_channels_from_given_val(response_desired_val)
            self._desired = self.CONFIG[self._product.type]["validator"](
                product, alias, raw
            )
            if self.color_mode in [1, 4]:
                self._white_value = int(raw[6:8], 16)
        else:
            raw = response_desired_val
            self._desired_raw = raw
            self._desired = self.CONFIG[self._product.type]["validator"](
                product, alias, raw
            )  # type: ignore
            if self.color_mode in [1, 4]:
                self._white_value = int(raw[6:8], 16)
        return raw

    @property
    def sensible_on_value(self) -> Any:
        """Return sensible on value in hass format."""
        if self.mask is not None:
            if int(self._last_on_state, 16) == 0:
                if self.color_mode in (BleboxColorMode.RGBW, BleboxColorMode.RGBorW):
                    return 255, 255, 255, 255
                if self.color_mode == BleboxColorMode.MONO:
                    return 255
                if self.color_mode in (BleboxColorMode.CT, BleboxColorMode.CTx2):
                    return 255, 255
            else:
                if self.color_mode == BleboxColorMode.MONO:
                    return self.rgb_hex_to_rgb_list(self._last_on_state)
                return self.normalise_elements_of_rgb(
                    self.rgb_hex_to_rgb_list(self._last_on_state)
                )
        else:
            if isinstance(self._last_on_state, str):
                if int(self._last_on_state, 16) == 0:
                    return [255] * len(self.rgb_hex_to_rgb_list(self._last_on_state))
                else:
                    if self.color_mode == BleboxColorMode.RGB:
                        return self.normalise_elements_of_rgb(
                            self.rgb_hex_to_rgb_list(self._last_on_state[:6])
                        )
                    elif self.color_mode == BleboxColorMode.MONO:
                        return self._last_on_state
                    else:
                        return self.rgb_hex_to_rgb_list(self._last_on_state)
            else:
                return self._last_on_state

    @property
    def rgb_hex(self) -> Any:
        """Return hex str representing rgb."""
        if isinstance(self._desired, int):
            return f"{self._desired:02x}"
        else:
            return self._desired

    @property
    def rgbw_hex(self) -> Any:
        return self._desired

    @property
    def rgbww_hex(self) -> Any:
        if len(self._desired) < 10:
            return None
        else:
            hex_str = self._desired
            hex_str_warm_cold = hex_str[6:]
            output_str = hex_str[0:6] + "".join(
                [
                    hex_str_warm_cold[i - 2 : i]
                    for i in range(len(hex_str_warm_cold), 0, -2)
                ]
            )
            return output_str

    @staticmethod
    def rgb_hex_to_rgb_list(hex_str) -> list[int]:
        """Return an RGB color value list from a hex color string."""
        if hex_str is not None:
            return [int(hex_str[i : i + 2], 16) for i in range(0, len(hex_str), 2)]
        return []

    @staticmethod
    def rgb_list_to_rgb_hex_list(rgb_list) -> hex:
        return [f"{i:02x}" for i in rgb_list]

    async def async_on(self, value: Any) -> None:
        if isinstance(value, (list, tuple)):
            if self.color_mode == BleboxColorMode.RGBWW:
                value.insert(3, value.pop())
            value = "".join(self.rgb_list_to_rgb_hex_list(value))
        if self.product.type == "dimmerBox":
            if not isinstance(value, int):
                value = int(value, 16)
        if not isinstance(value, type(self._off_value)):
            raise ValueError(
                f"turn_on called with bad parameter ({value} is {type(value)}, compared to {self._off_value} which is "
                f"{type(self._off_value)})"
            )

        if value == self._off_value:
            raise ValueError(f"turn_on called with invalid value ({value})")

        if self.mask is not None:
            value = self.mask(value)

        await self.async_api_command("set", value)

    async def async_off(self) -> None:
        if self.raw_value("colorMode") in [5, 6]:
            await self.async_api_command("set", self.mask("0000"))
        elif self.raw_value("colorMode") == 3 and self.product.type != "dimmerBox":
            await self.async_api_command("set", self.mask("00"))
        else:
            await self.async_api_command("set", self._off_value)
