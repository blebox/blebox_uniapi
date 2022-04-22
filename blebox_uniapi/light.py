from .feature import Feature
from .error import BadOnValueError
from typing import TYPE_CHECKING, Optional, Dict, Any, Union

if TYPE_CHECKING:
    from .box import Box


class Light(Feature):
    # TODO: better defaults?

    CONFIG = {
        "wLightBox": {
            "default": "FFFFFFFF",
            "off": "00000000",
            "brightness?": False,
            "white?": True,
            "color?": True,
            "to_value": lambda int_value: int_value,
            "validator": lambda product, alias, raw: product.expect_rgbw(alias, raw),
        },
        "wLightBoxS": {
            "default": "FF",
            "off": "00",
            "brightness?": True,
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
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: int_value,
            "validator": lambda product, alias, raw: product.expect_int(
                alias, raw, 255, 0
            ),
        },
    }

    def __init__(self, product: "Box", alias: str, methods: dict, extended_state: Optional[Dict]) -> None:
        super().__init__(product, alias, methods)

        config = self.CONFIG[product.type]
        print("Light init executed")
        self.extended_state = extended_state
        self._off_value = config["off"]
        self._last_on_state = self._default_on_value = config["default"]
        self.config_attribute_value("test")

    @property
    def supports_brightness(self) -> Any:
        return self.CONFIG[self._product.type]["brightness?"]

    @property
    def brightness(self) -> Optional[str]:
        return self._desired if self.supports_brightness else None

    def apply_brightness(self, value: int, brightness: int) -> Any:
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

        method = self.CONFIG[self._product.type]["to_value"]  # type: ignore
        # ok since not implemented for rgbw
        return method(brightness)  # type: ignore

    @property
    def supports_white(self) -> Any:
        return self.CONFIG[self._product.type]["white?"]

    @property
    def white_value(self) -> Optional[int]:
        return self._white_value

    def apply_white(self, value: str, white: int) -> Union[int, str]:
        if white is None:
            return value

        if not self.supports_white:
            return value

        rgbhex = value[0:6]
        white_raw = "{:02x}".format(white)
        return f"{rgbhex}{white_raw}"

    @property
    def supports_color(self) -> Any:
        return self.CONFIG[self._product.type]["color?"]

    def apply_color(self, value: str, rgb_hex: str) -> Union[int, str]:
        if rgb_hex is None:
            return value

        if not self.supports_color:
            return value

        white_hex = value[6:8]
        return f"{rgb_hex}{white_hex}"

    @property
    def is_on(self) -> Optional[bool]:
        return self._is_on

    def after_update(self) -> None:
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
        )  # type: ignore

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
    def sensible_on_value(self) -> Any:
        return self._last_on_state

    @property
    def rgbw_hex(self) -> Any:
        return self._desired

    async def async_on(self, value: Any) -> None:
        if not isinstance(value, type(self._off_value)):
            raise BadOnValueError(
                f"turn_on called with bad parameter ({value} is {type(value)}, compared to {self._off_value} which is {type(self._off_value)})"
            )

        if value == self._off_value:
            raise BadOnValueError(f"turn_on called with invalid value ({value})")

        await self.async_api_command("set", value)

    async def async_off(self) -> None:
        await self.async_api_command("set", self._off_value)

    def config_attribute_value(self, att_name: str) -> Union[None, str, list]:
        rgbw = self.extended_state.get("rgbw", None)
        if att_name == "_attr_effect_list":
            return [_.upper() for _ in list(rgbw['effectsNames'].values())]

        if att_name == "_attr_effect":
            effectid = str(rgbw.get("effectID", None))
            return rgbw.get("effectsNames")[effectid]
