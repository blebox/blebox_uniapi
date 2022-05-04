from datetime import timedelta

from .feature import Feature
from .error import BadOnValueError
from typing import TYPE_CHECKING, Optional, Dict, Any, Union

if TYPE_CHECKING:
    from .box import Box


class Light(Feature):
    # TODO: better defaults?
    CURRENT_CONF = dict()
    CONFIG = {
        "wLightBox": {
            "default": "FFFFFFFF",
            "off": "00000000",
            "brightness?": False,
            "color_temp?": False,
            "white?": True,
            "color?": True,
            "to_value": lambda int_value: int_value,
            "validator": lambda product, alias, raw: product.expect_rgbw(alias, raw),
        },
        "wLightBoxS": {
            "default": "FF",
            "off": "00",
            "brightness?": True,
            "color_temp?": False,
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
            "color_temp?": False,
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
            "off": "0000000000",
            "brightness?": True,
            "color_temp?": True,
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: "{:02x}".format(int_value),
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        }
    }

    def __init__(self, product: "Box", alias: str, methods: dict, extended_state: Optional[Dict], mask: Any) -> None:
        super().__init__(product, alias, methods)

        config = self.CONFIG[product.type]
        print(f"{mask=}")
        print(f"{config=}")
        # print(f"Uniapi Light init\n{self.unique_id}")
        self.mask = mask
        self.extended_state = extended_state
        rgbw = self.extended_state.get("rgbw", None)
        if rgbw.get('colorMode') == 6:
            config = self.COLOR_MODE_CONFIG["CT"]
        self.CURRENT_CONF = config
        print(f"color mode config: {config}")
        self._off_value = config["off"]
        self._last_on_state = self._default_on_value = config["default"]

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state) -> list["Light"]:
        # maska przekazywana w box type config dodatkowy klucza, a potem obsluzyc maskę
        # tu ma się wyjasnić ile tych instancji ma zostać zwrócone, najpierw dwa na sztywno
        print(f"many from conf: {box_type_config}")

        object_list = list()
        BLEBOX_COLOR_MODES = {
            1: "RGBW",
            2: "RGB",
            3: "MONO",
            4: "RGBorW",
            5: "CT", # colortemp, brightness, effect
            6: "CTx2", # colortemp, brightness, effect two instances
            7: "RGBWCCT"
        }

        ctx2 = {
                    "1": lambda x: f"{x}------",
                    "2": lambda x: f"----{x}--"
                    }

        print(f"colormode dict :{BLEBOX_COLOR_MODES[extended_state['rgbw']['colorMode']]}")
        if BLEBOX_COLOR_MODES[extended_state['rgbw']['colorMode']] == "CTx2":
            alias, methods = box_type_config[0]
            for indicator, mask in ctx2.items():
                object_list.append(cls(product, alias=alias + indicator, methods=methods, extended_state=extended_state, mask=mask)
                                   )
            return object_list

        return [cls(product, *args, extended_state=extended_state, mask=None) for args in box_type_config]

    # @property
    # def unique_id(self) -> str:
    #     return self.unique_id + self.mask

    @property
    def supports_brightness(self) -> Any:
        return self.CURRENT_CONF["brightness?"]
        # return self.CONFIG[self._product.type]["brightness?"]

    @property
    def supports_color_temp(self) -> Any:
        return self.CURRENT_CONF["color_temp?"]
        # return self.CONFIG[self._product.type]["color_temp?"]

    @property
    def brightness(self) -> Optional[str]:
        if self.raw_value("colorMode") in [6, 5]:
            _, bgt = self.color_temp_brightness_int_from_hex(self._desired)
            # print(f"{bgt=}")
            return bgt
        else:
            if self.supports_brightness:
                # print(f"desired:{self._desired}")
                return self._desired
            else:
                return None
        # return self._desired if self.supports_brightness else None

    @property
    def color_temp(self):
        ct, _ = self.color_temp_brightness_int_from_hex(self._desired)
        print(f"{ct=}\n{self}")
        return ct

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
        return self.CURRENT_CONF["white?"]
        # return self.CONFIG[self._product.type]["white?"]

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
        return self.CURRENT_CONF["color?"]
        # return self.CONFIG[self._product.type]["color?"]

    def apply_color(self, value: str, rgb_hex: str) -> Union[int, str]:
        if rgb_hex is None:
            return value

        if not self.supports_color:
            return value

        white_hex = value[6:8]
        return f"{rgb_hex}{white_hex}"

    def return_color_temp_with_brightness(self, value, brightness: Any) -> Optional[str]:
        # funkcja musi zwrócić HEXa z kolorem, z nałożonym brightness
        # Brightness pobrane z encji, HA wysyła pojedyncze słowniki z ustawieniem.
        # tutaj musi byc wykorzystana maska
        print(f"rctwb: {brightness}")
        value = value-1
        if value < 128:
            warm = min(255, value * 2)
            cold = 255
        else:
            warm = 255
            cold = max(0, min(255, (255 - value)))

        print(f"ret_col:\n{cold=}\n{warm=}\n{value=}")
        cold = cold * brightness/255
        warm = warm * brightness/255

        cold = "{:02x}".format(int(cold))
        warm = "{:02x}".format(int(warm))

        return self.mask(warm+cold)

    def current_value_for_selected_channels(self, mask_lambda):
        lambda_result = mask_lambda("xxxx")
        first_index = lambda_result.index("x")
        last_index = lambda_result.rindex("x")
        # print(f"raval 2;{self.raw_value('desired')=}")
        return self.raw_value("desired")[first_index:last_index+1]

    def color_temp_brightness_int_from_hex(self, val) -> (int, int):
        ''' Assuming that hex is 2channels, 4characters. Return values for front end'''
        # okreslic po ktorej stronie jest przesuniete i dostosować ze wspolczynnikiem swiatla
        # 1 rozbic na temp
        cold = int(val[2:], 16)
        warm = int(val[0:2], 16)
        print(f"CTB:\n{val=}\n{cold=}\n{warm=}\n{self}")
        if cold == warm:
            print("cw_qe")
            return 128, max(cold, warm)
        elif cold > warm:
            print("colder")
            return int(128*(warm/cold)), max(cold, warm)
        else:
            print(f"warmer:{int(128*((255-cold)/255)+128)}")
            return int(128*((255-cold)/255)+128), max(cold, warm)


    @property
    def is_on(self) -> Optional[bool]:
        return self._is_on

    @property
    def effect(self) -> Optional[str]:
        return self._effect

    def after_update(self) -> None:
        alias = self._alias
        product = self._product

        if product.last_data is None:
            self._desired_raw = None
            self._desired = None
            self._is_on = None
            if product.type == "wLightBox":
                self._white_value = None
                self._effect = None
            return
        if self.raw_value("colorMode") in [6, 5]: # sprawdzenie czy ct lub ct2
            # tryb 6
            raw = self.current_value_for_selected_channels(self.mask)
            self._desired = self.CONFIG[self._product.type]["validator"](
                product, alias, raw
            )
            print(f"{raw=}")
            # tryb 5(single)
        else:
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
        self._effect = self.raw_value("currentEffect")
        # if 'My wLightBox v3' in self.product.name:
        #     print(f"{product.name} last data:\n{product.last_data}\n method after_update() executed")

    @property
    def sensible_on_value(self) -> Any:
        return self._last_on_state

    @property
    def rgbw_hex(self) -> Any:
        return self._desired

    async def async_on(self, value: Any) -> None:
        print(f"async on validation:\nvalue:{value}\noff_val:{self._off_value}\n{type(self._off_value)}")
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
