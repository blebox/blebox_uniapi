class BadOnValueError(RuntimeError):
    pass


class Feature:
    def __init__(self, product, alias, methods):
        self._product = product
        self._alias = alias
        self._methods = methods

    @property
    def unique_id(self):
        return f"BleBox-{self._product.type}-{self._product.unique_id}-{self._alias}"

    async def async_update(self):
        await self._product.async_update_data()

    @property
    def full_name(self):
        return f"{self._product.type}-{self._alias}"

    @property
    def device_class(self):
        return self._device_class

    # TODO: (cleanup) move to product/box ?
    def raw_value(self, name):
        product = self._product

        # TODO: better exception?
        if product.last_data is None:
            raise RuntimeError("device state not available yet")

        methods = self._methods
        return product.follow(product.last_data, methods[name])


class AirQuality(Feature):
    def __init__(self, product, alias, methods):
        super().__init__(product, alias, methods)

    @property
    def pm1(self):
        return self._pm_value("pm1.value")

    @property
    def pm2_5(self):
        return self._pm_value("pm2_5.value")

    @property
    def pm10(self):
        return self._pm_value("pm10.value")

    def _pm_value(self, name):
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        raw = self.raw_value(name)
        if raw is None:  # no reading
            return None

        return product.expect_int(alias, raw, 3000, 0)


# TODO: rename to Sensor
class Sensor(Feature):
    @property
    def unit(self):
        return self._unit


class Temperature(Sensor):
    def __init__(self, product, alias, methods):
        super().__init__(product, alias, methods)
        self._unit = "celsius"
        self._device_class = "temperature"

    @property
    def current(self):
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        raw = self.raw_value("temperature")
        return product.expect_int(alias, raw, 12500, -5500) / 100.0


# TODO: handle tilt
class Cover(Feature):
    def __init__(self, product, alias, methods, dev_class):
        super().__init__(product, alias, methods)
        self._device_class = dev_class

    @property
    def current(self):
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        raw = self.raw_value("desired")
        return self._product.expect_int(alias, raw, 100, 0)

    @property
    def state(self):
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias

        if self._device_class == "shutter":
            raw = self.raw_value("state")
            return self._product.expect_int(alias, raw, 4, 0)
        elif self._device_class == "gate":
            raw = self.raw_value("state")
            return self._product.expect_int(alias, raw, 4, 0)
        elif self._device_class == "gatebox":  # gateBox
            # Reinterpret state to match shutterBox
            # NOTE: shutterBox is inverted (0 == closed), gateBox isn't
            current = self.raw_value("position")
            desired = self.raw_value("desired")

            # gate with gateBox visualized:
            #  (0) [   <#####] (100)

            if desired < current:
                return 0  # closing

            if desired > current:
                return 1  # opening

            if current == 0:  # closed
                return 3  # closed (lower/left limit)

            if current == 100:  # opened
                return 4  # open (upper/right limit)

            return 2  # manually stopped
        else:
            raise NotImplementedError

    @property
    def is_slider(self):
        if "shutter" == self._device_class:
            return True

        if "gate" == self._device_class:
            return True

        if "gatebox" == self._device_class:
            return False

        raise NotImplementedError

    @property
    def has_stop(self):
        if "shutter" == self._device_class:
            return True

        if "gate" == self._device_class:
            return True

        if "gatebox" == self._device_class:
            # TODO: (cleanup) add default value to raw_value() call
            product = self._product
            if product.last_data is None:
                return False

            alias = self._alias
            raw = self.raw_value("extraButtonType")
            return 1 == self._product.expect_int(alias, raw, 3, 0)

        raise NotImplementedError

    async def async_open(self):
        if self._device_class == "shutter":
            await self._product.async_api_command("open")
        elif "gate" == self._device_class:
            await self._product.async_api_command("open")
        elif self._device_class == "gatebox":  # gateBox
            await self._product.async_api_command("primary")
        else:
            raise NotImplementedError

    async def async_close(self):
        if self._device_class == "shutter":
            await self._product.async_api_command("close")
        elif "gate" == self._device_class:
            await self._product.async_api_command("close")
        elif self._device_class == "gatebox":  # gateBox
            await self._product.async_api_command("primary")
        else:
            raise NotImplementedError

    async def async_stop(self):
        if self._device_class == "shutter":
            await self._product.async_api_command("stop")
        elif "gate" == self._device_class:
            await self._product.async_api_command("stop")
        elif self._device_class == "gatebox":  # gateBox
            if self.has_stop:
                await self._product.async_api_command("secondary")
            else:
                raise RuntimeError("second button not configured as 'stop'")
        else:
            raise NotImplementedError

    async def async_set_position(self, value):
        if self._device_class == "shutter":
            await self._product.async_api_command("position", value)
        elif "gate" == self._device_class:
            await self._product.async_api_command("position", value)
        else:
            raise NotImplementedError


class Light(Feature):
    # TODO: better defaults?

    CONFIG = {
        "wLightBox": {
            "default": "FFFFFFFF",
            "off": "00000000",
            "brightness?": False,
            "white?": True,
            "color?": True,
            "validator": lambda product, alias, raw: product.expect_rgbw(alias, raw),
        },
        "wLightBoxS": {
            "default": "FF",
            "off": "00",
            "brightness?": True,
            "white?": False,
            "color?": False,
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

        self._update_state()

    @property
    def supports_brightness(self):
        return self.CONFIG[self._product.type]["brightness?"]

    @property
    def brightness(self):
        return self._desired if self.supports_brightness else None

    def apply_brightness(self, value, brightness):
        if brightness is None:
            return value

        if not self.supports_brightness:
            return value

        return brightness  # ok since not implemented for rgbw

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
        return self._desired_raw != self._off_value

    async def async_update(self):
        await super().async_update()

        self._update_state()

    def _update_state(self):
        alias = self._alias
        product = self._product
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

    @property
    def sensible_on_value(self):
        return self._last_on_state

    @property
    def rgbw_hex(self):
        return self._desired

    async def async_on(self, value):
        product = self._product
        if value == self._off_value:
            raise BadOnValueError(value)

        await product.async_api_command("set", value)
        self._update_state()

    async def async_off(self, **kwargs):
        product = self._product
        await product.async_api_command("set", self._off_value)
        self._update_state()


# TODO: rename to Thermo?
class Climate(Feature):
    @property
    def is_on(self):
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        raw = self.raw_value("state")
        if raw is None:  # no reading
            return None

        return 1 == product.expect_int(alias, raw, 1, 0)

    @property
    def desired(self):
        return self._read_temperature("desired")

    @property
    def current(self):
        return self._read_temperature("temperature")

    @property
    def is_heating(self):
        product = self._product
        if not product.last_data:
            return None

        return self.is_on and (self.current < self.desired)

    async def async_on(self):
        await self._product.async_api_command("on")

    async def async_off(self):
        await self._product.async_api_command("off")

    # TODO: use as attribute in product config
    def _read_temperature(self, field):
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        raw = self.raw_value(field)
        if raw is None:  # no reading
            return None

        return round(product.expect_int(alias, raw, 12500, -5500) / 100.0, 1)

    async def async_set_temperature(self, value):
        await self._product.async_api_command("set", int(round(value * 100.0)))


class Switch(Feature):
    def __init__(self, product, alias, methods, dev_class, unit_id=None):
        super().__init__(product, alias, methods)
        self._device_class = dev_class
        self._unit_id = unit_id

    @property
    def is_on(self):
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        raw = self.raw_value("state")
        if raw is None:  # no reading
            return None

        return 1 == product.expect_int(alias, raw, 1, 0)

    @property
    def _unit_args(self):
        unit = self._unit_id
        return [] if unit is None else [unit]

    async def async_turn_on(self, **kwargs):
        await self._product.async_api_command("on", *self._unit_args)

    async def async_turn_off(self, **kwargs):
        await self._product.async_api_command("off", *self._unit_args)
