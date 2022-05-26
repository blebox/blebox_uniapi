import traceback
from datetime import timedelta

from enum import IntEnum
from .feature import Feature
from .error import BadOnValueError
from typing import TYPE_CHECKING, Optional, Dict, Any, Union, Iterable

if TYPE_CHECKING:
    from .box import Box

BLEBOX_COLOR_MODES = {
            1: "RGBW",    # RGB color-space with color brightness, white brightness
            2: "RGB",     # RGB color-space with color brightness
            3: "MONO",
            4: "RGBorW",  # RGBW entity, where white color is prioritised
            5: "CT",      # color-temperature, brightness, effect
            6: "CTx2",    # color-temperature, brightness, effect, two instances
            7: "RGBWW"    # RGB with two color-temperature sliders(warm, cold)
        }


class BleboxColorMode(IntEnum):
        RGBW = 1
        RGB = 2
        MONO = 3
        RGBorW = 4
        CT = 5
        CTx2 = 6
        RGBWW = 7


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
            "to_value": lambda int_value: f"{int_value:02x}",
            "validator": lambda product, alias, raw: product.expect_rgbw(alias, raw),
        },
        "wLightBoxS": {
            "default": "FF",
            "off": "00",
            "brightness?": True,
            "color_temp?": False,
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
            "to_value": lambda int_value: f"{int_value:02x}",
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
            "to_value": lambda int_value: f"{int_value:02x}",
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
            "to_value": lambda int_value: f"{int_value:02x}",
            "validator": lambda product, alias, raw: product.expect_hex_str(
                alias, raw, 255, 0
            ),
        }
    }

    def __init__(self, product: "Box", alias: str, methods: dict, extended_state: Optional[Dict], mask: Any,
                 desired_color, color_mode, effect_list, current_effect) -> None:
        super().__init__(product, alias, methods)
        # Todo Implement DRY
        config = self.CONFIG[product.type]
        self.mask = mask
        #---------------- dodanie do initu
        self.desired_color = desired_color
        self._color_mode = color_mode
        self._effect_list = effect_list
        if self._effect_list is not None:
            self._effect = effect_list.get(str(current_effect), None)

        # okreslenie color_mode istotne, jezeli nie ma extended state
        # init powinien byc prosty i nie powinien zbednie wyliczac, powinien odstac przekazane parammetry juz gotowe
        # , nie powinno byc tu w ogole extended state

        if extended_state not in [None, {}]:
            self.extended_state = extended_state
            rgbw = self.extended_state.get("rgbw", None)
            self.device_colorMode = color_mode
            if self.device_colorMode in [6,7]:
                config = self.COLOR_MODE_CONFIG[BLEBOX_COLOR_MODES[self.device_colorMode]]
        else:
            if product.type == 'dimmerBox':
                self.device_colorMode = BleboxColorMode.MONO
        self.CURRENT_CONF = config

        self._off_value = self.evaluate_off_value(config, desired_color)
        self._last_on_state = self._default_on_value = config["default"]

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state) -> list["Light"]:
        # maska przekazywana w box type config dodatkowy klucza, a potem obsluzyc maskę
        # tu ma się wyjasnić ile tych instancji ma zostać zwrócone, najpierw dwa na sztywno
        # tutaj kontrola instancji, masek, typu color mode dla frontu
        # tutaj extended state powuinien wyciagac wszystkie informacje

        if isinstance(extended_state, dict) and extended_state is not None:
            desired_color = extended_state.get('rgbw', {}).get('desiredColor', None)
            color_mode = extended_state.get('rgbw', {}).get('colorMode', None)
            current_effect = extended_state.get('rgbw', {}).get('effectID', None)
            effect_list = extended_state.get('rgbw', {}).get('effectsNames', None)
        else:
            desired_color = None
            color_mode = None
            current_effect = None
            effect_list = None

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

        if extended_state is not None and color_mode is not None:
            if BleboxColorMode(color_mode).name == "RGBW":
                alias, methods = box_type_config[0]
                return [
                    cls(product, alias=alias + "_RGBW", methods=methods, extended_state=extended_state,
                        mask=lambda x: f"{x}--", desired_color=desired_color, color_mode=color_mode,
                        current_effect=current_effect, effect_list=effect_list)]

            if BleboxColorMode(color_mode).name == "RGB":
                alias, methods = box_type_config[0]
                return [
                    cls(product, alias=alias + "_RGB", methods=methods, extended_state=extended_state,
                        mask=None, desired_color=desired_color, color_mode=color_mode,  # mask = lambda x: f"{x}----"
                        current_effect=current_effect, effect_list=effect_list)]

            if BleboxColorMode(color_mode).name == "MONO":
                if len(desired_color) % 2 == 0:
                    alias, methods = box_type_config[0]
                    mono = list(mono.items())
                    for i in range(0, int(len(desired_color) / 2)):
                        indicator, mask = mono[i]
                        object_list.append(
                            cls(product, alias=alias + "_" + indicator, methods=methods, extended_state=extended_state,
                                mask=mask, desired_color=desired_color, color_mode=color_mode, current_effect=current_effect,
                                effect_list=effect_list)
                        )
                    return object_list

            if BleboxColorMode(color_mode).name == "RGBorW":
                alias, methods = box_type_config[0]
                return [
                    cls(product, alias=alias + "_RGBorW", methods=methods, extended_state=extended_state, mask=None,
                        desired_color=desired_color, color_mode=color_mode, current_effect=current_effect,
                        effect_list=effect_list)]

            if BleboxColorMode(color_mode).name == "CT":
                alias, methods = box_type_config[0]
                mask = ctx2["cct1"]
                return [cls(product, alias=alias + "_cct", methods=methods, extended_state=extended_state, mask=mask,
                        desired_color=desired_color, color_mode=color_mode, current_effect=current_effect,
                        effect_list=effect_list)]

            if BleboxColorMode(color_mode).name == "CTx2":
                alias, methods = box_type_config[0]
                for indicator, mask in ctx2.items():
                    object_list.append(
                        cls(product, alias=alias + "_" + indicator, methods=methods, extended_state=extended_state,
                            mask=mask, desired_color=desired_color, color_mode=color_mode, current_effect=current_effect
                            , effect_list=effect_list)
                                       )
                return object_list

            if BleboxColorMode(color_mode).name == "RGBWW":
                alias, methods = box_type_config[0]
                return [
                    cls(product, alias=alias + "_RGBCCT", methods=methods, extended_state=extended_state, mask=None,
                        desired_color=desired_color, color_mode=color_mode, current_effect=current_effect,
                        effect_list=effect_list)]

        if len(box_type_config) > 0:
            if "Brightness" in box_type_config[0][1].get('desired'):
                color_mode = BleboxColorMode.MONO
            return [cls(product, *args, extended_state=extended_state, mask=None, desired_color=desired_color,
                        color_mode=color_mode, current_effect=current_effect, effect_list=effect_list)
                    for args in box_type_config]
        else:
            return []

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
            return bgt
        # elif self.color_mode == BleboxColorMode.RGB:
        #     return 255
        else:
            return self.evaluate_brightness_from_rgb(self.rgb_hex_to_rgb_list(self.rgb_hex))

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

    def evaluate_brightness_from_rgb(self, iterable) -> int:
        "return brightness from 0 to 255 evaluated basing rgb"
        return int(max(iterable))


    def apply_brightness(self, value: int, brightness: int) -> Any:
        '''Return list of values with applied brightness.'''
        if self.product.type == 'dimmerBox' or self.color_mode == BleboxColorMode.MONO:
            return [brightness]
        if brightness is None:
            return [value]
        if not isinstance(brightness, int):
            raise BadOnValueError(
                f"adjust_brightness called with bad parameter ({brightness} is {type(value)} instead of int)"
            )

        if brightness > 255:
            raise BadOnValueError(
                f"adjust_brightness called with bad parameter ({brightness} is greater than 255)"
            )
        #anon_fun = lambda x: round(x * (brightness / 255))
        res = list(map(lambda x: round(x * (brightness / 255)), value))
        return res
        # return "".join(self.rgb_list_to_rgb_hex(res))

    def evaluate_off_value(self, config: dict, raw_hex: str) -> str:
        '''
        Returns hex representing off state value without mask formatting for necessary channels if mask is applied.
        If no mask applied than returns default from config

        :param config:
        :param raw_hex:
        :return: str
        '''
        if self.mask:
            return "0"*(len(raw_hex) - len(self.mask('x').replace('x', '')))
        elif raw_hex is not None:
            if len(raw_hex) < len(config['off']):
                return config["off"][:len(raw_hex)]
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
        white_raw = f"{white:02x}"
        return f"{rgbhex}{white_raw}"

    @property
    def supports_color(self) -> Any:
        return self.CURRENT_CONF["color?"]
        # return self.CONFIG[self._product.type]["color?"]

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


    def return_color_temp_with_brightness(self, value, brightness: Any) -> Optional[str]:
        ''' Method returns value which will be send to  '''
        if value < 128:
            warm = min(255, value * 2)
            cold = 255
        else:
            warm = 255
            cold = max(0, min(255, (255-value) * 2))
        cold = cold * brightness/255
        warm = warm * brightness/255
        cold = f"{int(round(cold)):02x}"
        warm = f"{int(round(warm)):02x}"

        return warm+cold

    def value_for_selected_channels_from_given_val(self, value: str):
        if self.color_mode in [BleboxColorMode.CT, BleboxColorMode.CTx2]:
            lambda_result = self.mask("xxxx")
        elif self.color_mode == BleboxColorMode.MONO:
            lambda_result = self.mask("xx")
        elif self.color_mode == BleboxColorMode.RGB:
            lambda_result = self.mask("xxxxxx")
        elif self.color_mode == BleboxColorMode.RGBW:
            lambda_result = self.mask("xxxxxxxx")
        first_index = lambda_result.index("x")
        last_index = lambda_result.rindex("x")
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

    def normalise_elements_of_rgb(self, elements):
        max_val = max(elements)
        if 0 > max_val > 255:
            raise BadOnValueError(f"Max value in normalisation was outside range {max_val}.")
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
        # requires refactor in context when mask is applied
        # do I know here what is device mod?

        alias = self._alias
        product = self._product

        if product.last_data is None:
            self._desired_raw = None        # wartsc oczekiwana nie przetworzona
            self._desired = None            # wartosc oczekiwana
            self._is_on = None              # bool czy urzadzenie jest wlaczone
            self._effect = None             # wartos pola effect
            if self.mask is None:
                self._white_value = None    # wartosc kanalu bialego
            return
        self._effect = self.raw_value("currentEffect")

        raw = self._return_desired_value(alias, product)

        # reguła jeżeli po ustaweieniu wartość jest wartoscia OFF:
        # jezeli wartosc raw jest wartoscia off to nie aktualizwac ?

        self._set_last_on_value(alias, product, raw)

        self._set_is_on()

    def _set_last_on_value(self, alias, product, raw):
        if raw == self._off_value:
            if product.type == "wLightBox":  # jezeli urzadzenie typu wLightBox ma wyciagnac last_color
                raw = product.expect_rgbw(alias, self.raw_value("last_color"))
                if self.mask is not None:
                    raw = self.value_for_selected_channels_from_given_val(raw)
                if raw == self._off_value:
                    raw = self.value_for_selected_channels_from_given_val("ffffffffff")
            else:
                raw = self._default_on_value
        if raw in (self._off_value, None):
            raise BadOnValueError(raw)
        # TODO: store as custom value permanently (exposed by API consumer)
        self._last_on_state = raw

    def _set_is_on(self):
        if self.mask is not None:
            self._is_on = (self._desired != self._off_value) or (self._effect != 0 and self._effect is not None)
        elif self.raw_value("colorMode") == 7:
            self._is_on = (self._desired != self._off_value) or (self._effect != 0 and self._effect is not None)
        else:
            self._is_on = (self._desired != self._off_value) or (self._effect != 0 and self._effect is not None)

    def _return_desired_value(self, alias, product) -> str:
        '''
        Return value representing desired device state, set desired fields
        :param alias:
        :param product:
        :return desired value including mask:
        '''
        # zrefaktoryzować żeby wywoływać _return_desired_value bez parametrów i nie zwracac
        response_desired_val = self.raw_value("desired")
        if self.mask is not None:
            raw = self.value_for_selected_channels_from_given_val(response_desired_val)
            self._desired = self.CONFIG[self._product.type]["validator"](
                product, alias, raw
            )
        else:
            raw = response_desired_val
            self._desired_raw = raw
            self._desired = self.CONFIG[self._product.type]["validator"](
                product, alias, raw
            )  # type: ignore
            if self.color_mode in [1, 4]:  # wpowadzic stale, ENUM wprowadzic wymienic z int na te enu,
                self._white_value = int(raw[6:8], 16)
        return raw

    @property
    def sensible_on_value(self) -> Any:
        ''' Return sensible on value in hass format. '''
        if self.mask is not None:
            if int(self._last_on_state, 16) == 0:
                if self.color_mode in (BleboxColorMode.RGBW, BleboxColorMode.RGBorW):
                    return 255, 255, 255, 255
                if self.color_mode == BleboxColorMode.RGB:
                    return 255, 255, 255
                if self.color_mode == BleboxColorMode.MONO:
                    return 255
                if self.color_mode in (BleboxColorMode.CT, BleboxColorMode.CTx2):
                    return 255, 255
                if self.color_mode == BleboxColorMode.RGBWW:
                    return 255, 255, 255, 255, 255
            else:
                rgb_hex = self.value_for_selected_channels_from_given_val(self._last_on_state)
                if self.color_mode == BleboxColorMode.MONO:
                    return self.rgb_hex_to_rgb_list(self._last_on_state)
                return self.normalise_elements_of_rgb(self.rgb_hex_to_rgb_list(self._last_on_state))
        else:
            if self.color_mode == BleboxColorMode.RGB:
                return self.normalise_elements_of_rgb(self.rgb_hex_to_rgb_list(self._last_on_state[:6]))
            elif self.color_mode == BleboxColorMode.MONO:
                return self._last_on_state
            else:
                return self.normalise_elements_of_rgb(self.rgb_hex_to_rgb_list(self._last_on_state))

    @property
    def rgb_hex(self) -> Any:
        '''Return hex str representing rgb'''
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
            output_str = hex_str[0:6] + "".join([hex_str_warm_cold[i - 2:i] for i in range(len(hex_str_warm_cold), 0, -2)])
            return output_str

    @classmethod
    def rgb_hex_to_rgb_list(cls, hex_str) -> list[int]:
        """Return an RGB color value list from a hex color string."""
        if hex_str is not None:
            return [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]
        return []

    @classmethod
    def rgb_list_to_rgb_hex_list(cls, rgb_list) -> hex:
        return [f"{i:02x}" for i in rgb_list]

    async def async_on(self, value: Any) -> None:
        if isinstance(value, Iterable):
            if self.color_mode == BleboxColorMode.RGBWW:
                value.insert(3, value.pop())
            value = "".join(self.rgb_list_to_rgb_hex_list(value))
        if self.product.type == "dimmerBox":
            value = int(value, 16)
        if not isinstance(value, type(self._off_value)):
            raise BadOnValueError(
                f"turn_on called with bad parameter ({value} is {type(value)}, compared to {self._off_value} which is "
                f"{type(self._off_value)})"
            )

        if value == self._off_value:
            raise BadOnValueError(f"turn_on called with invalid value ({value})")

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

    def config_attribute_value(self, att_name: str) -> Union[None, str, list]:
        if self.extended_state is None:
            return None
        rgbw = self.extended_state.get("rgbw", None)
        if att_name == "_attr_effect_list":
            return [_.upper() for _ in list(rgbw['effectsNames'].values())]

        if att_name == "_attr_effect":
            effectid = str(rgbw.get("effectID", None))
            return rgbw.get("effectsNames")[effectid]
