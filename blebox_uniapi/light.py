import traceback
from datetime import timedelta

from .feature import Feature
from .error import BadOnValueError
from typing import TYPE_CHECKING, Optional, Dict, Any, Union

if TYPE_CHECKING:
    from .box import Box

BLEBOX_COLOR_MODES = {
            1: "RGBW", #rgb pallet with color brightness, white brightness
            2: "RGB", #rgb pallet with color brightness
            3: "MONO",
            4: "RGBorW", # rgbw dac w jedno entity rgbw, i obsługę
            5: "CT", # colortemp, brightness, effect
            6: "CTx2", # colortemp, brightness, effect two instances CTx2
            7: "RGBWW" #RGBWCT
        }


class Light(Feature):
    # TODO: better defaults?
    CURRENT_CONF = dict()
    CONFIG = {
        "wLightBox": {
            "default": "FFFFFFFFFF",
            "off": "0000000000",
            "brightness?": True,
            "color_temp?": False,
            "white?": True,
            "color?": True,
            "to_value": lambda int_value: "{:02x}".format(int_value),
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
            "off": "0000",
            "brightness?": True,
            "color_temp?": True,
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: "{:02x}".format(int_value),
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        },
        "CTx2": {
            "default": "FFFFFFFF",
            "off": "0000",
            "brightness?": True,
            "color_temp?": True,
            "white?": False,
            "color?": False,
            "to_value": lambda int_value: "{:02x}".format(int_value),
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        },
        "RGBWW":{
            "default": "FFFFFFFFFF",
            "off": "0000000000",
            "brightness?": True,
            "color_temp?": False,
            "white?": True,
            "color?": True,
            "to_value": lambda int_value: "{:02x}".format(int_value),
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        }
    }

    def __init__(self, product: "Box", alias: str, methods: dict, extended_state: Optional[Dict], mask: Any) -> None:
        super().__init__(product, alias, methods)
        # Todo Implement DRY
        config = self.CONFIG[product.type]
        # print(f"Uniapi Light init\n{self.unique_id}")
        self.mask = mask
        self.extended_state = extended_state
        rgbw = self.extended_state.get("rgbw", None)
        self.device_colorMode = rgbw.get('colorMode', None)

        if self.device_colorMode in [6,7]:
            config = self.COLOR_MODE_CONFIG[BLEBOX_COLOR_MODES[self.device_colorMode]]
        self.CURRENT_CONF = config

        des_color = rgbw.get("desiredColor", None)
        self._off_value = self.evaluate_off_value(config, des_color)
        self._last_on_state = self._default_on_value = config["default"]

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state) -> list["Light"]:
        # maska przekazywana w box type config dodatkowy klucza, a potem obsluzyc maskę
        # tu ma się wyjasnić ile tych instancji ma zostać zwrócone, najpierw dwa na sztywno
        # tutaj kontrola instancji, masek, typu color mode dla frontu
        if isinstance(extended_state, dict) and extended_state != {}:
            color_mod_integer = extended_state.get('rgbw', {}).get('colorMode')
            desired_color = extended_state.get('rgbw', {}).get('desiredColor')
        object_list = list()

        ctx2 = {
                    "cct1": lambda x: f"{x}------",
                    "cct2": lambda x: f"----{x}--"
                    }
        mono = {
            "mono1": lambda x: f"{x}------",
            "mono2": lambda x: f"--{x}----",
            "mono3": lambda x: f"----{x}--",
            "mono4": lambda x: f"------{x}",
        }


        if extended_state != {}:
            if BLEBOX_COLOR_MODES[color_mod_integer] == "CTx2":
                alias, methods = box_type_config[0]
                for indicator, mask in ctx2.items():
                    print(f"{indicator=}")
                    object_list.append(cls(product, alias=alias + "_" + indicator, methods=methods,
                                           extended_state=extended_state, mask=mask)
                                       )
                return object_list
            if BLEBOX_COLOR_MODES[color_mod_integer] == "CT":
                alias, methods = box_type_config[0]
                mask = ctx2["cct1"]
                return [cls(product, alias=alias + "_cct", methods=methods, extended_state=extended_state, mask=mask)]
            if BLEBOX_COLOR_MODES[color_mod_integer] == "MONO":
                if len(desired_color) % 2 == 0:
                    alias, methods = box_type_config[0]
                    mono = list(mono.items())
                    for i in range(0,int(len(desired_color)/2)):
                        indicator, mask = mono[i]
                        object_list.append(
                            cls(product, alias=alias + "_" + indicator, methods=methods, extended_state=extended_state,
                                mask=mask)
                            )
                    return object_list

        # dodac szczególny przypadek gdy color mode RGBorW(4) wstawic nowa klase

        return [cls(product, *args, extended_state=extended_state, mask=None) for args in box_type_config]

    # lepsza obsługa colorMode (wybieranie), czy zawze musi byc konifg?

    @property
    def supports_brightness(self) -> Any:
        return self.CURRENT_CONF["brightness?"]

    @property
    def supports_color_temp(self) -> Any:
        return self.CURRENT_CONF["color_temp?"]

    @property
    def brightness(self) -> Optional[str]:
        if self.color_mode in [6, 5]:
            _, bgt = self.color_temp_brightness_int_from_hex(self._desired)
            print(f"{bgt=}")
            return bgt
        else:
            return self.evaluate_brightness_from_rgb(self.rgb_hex_to_rgb_list(self.rgb_hex))

    @property
    def color_temp(self):
        ct, _ = self.color_temp_brightness_int_from_hex(self._desired)
        return ct

    def evaluate_brightness_from_rgb(self, iterable) -> int:
        "return brightness from 0 to 255 evaluated basing rgb"
        return max(iterable)


    def apply_brightness(self, value: int, brightness: int) -> Any:
        if brightness is None:
            return value
        print(f"apply brightness:\n{value=}\n{brightness=}")
        if not isinstance(brightness, int):
            raise BadOnValueError(
                f"adjust_brightness called with bad parameter ({brightness} is {type(value)} instead of int)"
            )

        if brightness > 255:
            raise BadOnValueError(
                f"adjust_brightness called with bad parameter ({brightness} is greater than 255)"
            )

        anon_fun = lambda x: round(x * (brightness / 255))
        res = list(map(anon_fun, self.rgb_hex_to_rgb_list(value)))
        print(f"{res=}")
        return "".join(self.rgb_list_to_rgb_hex(res))

    def evaluate_off_value(self, config: dict, raw_hex: str) -> str:
        '''
        Returns hex representing off state value without mask formatting for necessary channels if mask is applied.
        If no mask applied than returns default from config

        :param config:
        :param raw_hex:
        :return: str
        '''
        '''  '''
        print(f"{self.full_name}eofv: {self.mask=}\n {config}")
        if self.mask:
            return "0"*(len(raw_hex) - len(self.mask('x').replace('x', '')))
        else:
            return config["off"]

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

    @property
    def color_mode(self) -> int:
        return self.device_colorMode

    def apply_color(self, value: str, rgb_hex: str) -> Union[int, str]:
        if rgb_hex is None:
            return value

        if not self.supports_color:
            return value

        white_hex = value[6:8]
        return f"{rgb_hex}{white_hex}"

    def return_color_temp_with_brightness(self, value, brightness: Any) -> Optional[str]:
        ''' Method returns value which will be send to  '''
        if value < 128:
            warm = min(255, value * 2)
            cold = 255
        else:
            warm = 255
            cold = max(0, min(255, (255-value) * 2))
        print(f"{cold=}\n{warm=}\n{brightness=}")
        cold = cold * brightness/255
        warm = warm * brightness/255
        print(f"Wartosci do hexa:\n\tin:\n\t{value=}\n\t{brightness=}\n\tout:\n\t{cold=}\n\t{warm=}")
        cold = "{:02x}".format(int(round(cold)))
        warm = "{:02x}".format(int(round(warm)))

        return warm+cold

    def value_for_selected_channels_from_given_val(self, value: str):
        if self.color_mode in [5,6]:
            lambda_result = self.mask("xxxx")
        elif self.color_mode == 3:
            lambda_result = self.mask("xx")
        first_index = lambda_result.index("x")
        last_index = lambda_result.rindex("x")
        print(f"vfscfgv: {value[first_index:last_index+1]}\n{value}")
        return value[first_index:last_index+1]

    def color_temp_brightness_int_from_hex(self, val) -> (int, int):
        ''' Assuming that hex is 2channels, 4characters. Return values for front end'''
        # okreslic po ktorej stronie jest przesuniete i dostosować ze wspolczynnikiem swiatla
        # 1 rozbic na temp
        # 2 wyznaczyc brigtness
        # 3 sprowadzic do wartosci tak jak przy 100% brightness

        cold = int(val[2:], 16)
        warm = int(val[0:2], 16)

        if cold > warm:
            # print("colder")
            if warm == 0:
                return 0, cold
            else:
                return round(int((128 * (warm * 255/cold)/255)), 2), cold
        if cold < warm:
            if cold == 0:
                return 255, warm
            else:
                return round(int(255 - 128 * (cold * (255/warm)/255)), 2), warm
        else:
            return 128, max(cold, warm)


    @property
    def is_on(self) -> Optional[bool]:
        return self._is_on

    @property
    def effect(self) -> Optional[str]:
        return self._effect

    def after_update(self) -> None:
        # requires refactor in context when mask is applied
        # do I know here what is device mod?

        alias = self._alias
        product = self._product

        if product.last_data is None:
            self._desired_raw = None     # wartsc oczekiwana nie przetworzona
            self._desired = None         # wartosc oczekiwana
            self._is_on = None           # bool czy urzadzenie jest wlaczone
            if self.mask is None:
                self._white_value = None # wartosc kanalu bialego
                self._effect = None      # wartos pola effect
            return

        self._effect = self.raw_value("currentEffect")

        # todo ustalenie wartosci raw
        if self.mask is not None: # sprawdzenie czy ct lub ct2
            # tryb 6
            raw = self.value_for_selected_channels_from_given_val(self.raw_value("desired"))
            self._desired = self.CONFIG[self._product.type]["validator"](
                product, alias, raw
            )
            # tryb 5(single)
            print(f"{self._off_value=}")
        else:
            raw = self.raw_value("desired")
            self._desired_raw = raw
            self._desired = self.CONFIG[self._product.type]["validator"](
                product, alias, raw
            )  # type: ignore
            if self.color_mode in [1, 4]:
                self._white_value = int(raw[6:8], 16)

        #reguła jeżeli po ustaweieniu wartość jest wartoscia OFF:
        # jezeli wartosc raw jest wartoscia off
        if raw == self._off_value:
            if product.type == "wLightBox":
                raw = product.expect_rgbw(alias, self.raw_value("last_color"))
                print(f"raw if wLightBox from last on: {raw}")
                if self.mask is not None:
                    raw = self.value_for_selected_channels_from_given_val(raw)
                if raw == self._off_value:
                    raw = self.value_for_selected_channels_from_given_val("ffffffffff")
            else:
                print(f"{self._default_on_value}")
                raw = self._default_on_value

        if raw in (self._off_value, None):
            raise BadOnValueError(raw)

        # TODO: store as custom value permanently (exposed by API consumer)
        self._last_on_state = raw
        if self.mask is not None:
            self._is_on = self._desired != self._off_value
            print(f"IS ON CHECK\n{self._off_value=}\n{self._desired=}\n{self._is_on=}")
        elif self.raw_value("colorMode") == 7:
            self._is_on = (self._desired != self._off_value) or self._effect != 0
        else:
            self._is_on = (self._desired != self._off_value) or self._effect != 0
        print(f"{self.full_name} is on: {self._is_on}.\nlast on val: {self._last_on_state}\n{self._off_value}\n{self._desired}")

        # print(f"-------------\n{product.type=}\n{product.name}\nAFTER_UPDATE set:\n{self._desired_raw=}\n{self._desired=}\n{self._is_on=}\n{self._white_value=}\n{self._effect=}\n{self._last_on_state=}\n-------------")

    @property
    def sensible_on_value(self) -> Any:
        if self.mask is not None:
            print(f"{self._last_on_state=}")
            if self.color_mode == 3:
                if int(self._last_on_state, 16) == 0:
                    return "ff"
            # return self.value_for_selected_channels_from_given_val(self._last_on_state)
        return self._last_on_state

    @property
    def rgb_hex(self) -> Any:
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
            output_str = hex_str[0:6] + "".join([hex_str_warm_cold[i - 2:i] for i in range(len(hex_str_warm_cold), 0, -2)])
            return output_str

    @classmethod
    def rgb_hex_to_rgb_list(cls, hex_str):
        """Return an RGB color value list from a hex color string."""
        print(f"{hex_str}")
        return [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]

    @classmethod
    def rgb_list_to_rgb_hex(cls, rgb_list) -> hex:
        print(f"{rgb_list=}")
        return ["{:02x}".format(i) for i in rgb_list]

    async def async_on(self, value: Any) -> None:
        print(f"async on validation:\nvalue:{value}\noff_val:{self._off_value}\n{type(self._off_value)}")
        if not isinstance(value, type(self._off_value)):
            raise BadOnValueError(
                f"turn_on called with bad parameter ({value} is {type(value)}, compared to {self._off_value} which is {type(self._off_value)})"
            )

        if value == self._off_value:
            raise BadOnValueError(f"turn_on called with invalid value ({value})")

        if self.mask is not None:
            value = self.mask(value)

        await self.async_api_command("set", value)

    async def async_off(self) -> None:
        if self.raw_value("colorMode") in [5, 6]:
            await self.async_api_command("set", self.mask("0000"))
            print(f"sent value: {self.mask('0000')}")
        elif self.raw_value("colorMode") == 3:
            await self.async_api_command("set", self.mask("00"))
            print(f"sent value: {self.mask('00')}")
        else:
            await self.async_api_command("set", self._off_value)

    def config_attribute_value(self, att_name: str) -> Union[None, str, list]:
        rgbw = self.extended_state.get("rgbw", None)
        if att_name == "_attr_effect_list":
            return [_.upper() for _ in list(rgbw['effectsNames'].values())]

        if att_name == "_attr_effect":
            effectid = str(rgbw.get("effectID", None))
            return rgbw.get("effectsNames")[effectid]
