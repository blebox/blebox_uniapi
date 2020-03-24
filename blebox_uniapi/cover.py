from .error import MisconfiguredDevice, DeviceStateNotAvailable
from .feature import Feature


class Slider:
    def read_state(self, alias, raw_value, product):
        raw = raw_value("state")
        return product.expect_int(alias, raw, 4, 0)

    @property
    def is_slider(self):
        return True

    @property
    def open_command(self):
        return "open"

    @property
    def close_command(self):
        return "close"

    def stop_command(self, has_stop):
        return "stop"

    def read_has_stop(self, alias, raw_value, product):
        return True


class Shutter(Slider):
    @property
    def min_position(self):
        return -1


class Gate(Slider):
    @property
    def min_position(self):
        return 0


class GateBox:
    @property
    def is_slider(self):
        return False

    @property
    def min_position(self):
        return 0

    @property
    def min_position(self):
        return -1  # "unknown"

    @property
    def open_command(self):
        return "primary"

    @property
    def close_command(self):
        return "primary"

    def read_state(self, alias, raw_value, product):
        # Reinterpret state to match shutterBox
        # NOTE: shutterBox is inverted (0 == closed), gateBox isn't
        current = raw_value("position")
        desired = raw_value("desired")

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

    def stop_command(self, has_stop):
        if not has_stop:
            raise MisconfiguredDevice("second button not configured as 'stop'")
        return "secondary"

    def read_has_stop(self, alias, raw_value, product):
        if product.last_data is None:
            return False

        raw = raw_value("extraButtonType")
        return 1 == product.expect_int(alias, raw, 3, 0)


# TODO: handle tilt
class Cover(Feature):
    ATTR_CLASS_MAP = {"shutter": Shutter, "gate": Gate, "gatebox": GateBox}

    def __init__(self, product, alias, methods, dev_class):
        self._device_class = dev_class
        self._attributes = self.ATTR_CLASS_MAP[self._device_class]()
        super().__init__(product, alias, methods)

    @property
    def current(self):
        return self._desired

    @property
    def state(self):
        return self._state

    @property
    def is_slider(self):
        return self._attributes.is_slider

    @property
    def has_stop(self):
        return self._has_stop

    async def async_open(self):
        await self.async_api_command(self._attributes.open_command)

    async def async_close(self):
        await self.async_api_command(self._attributes.close_command)

    async def async_stop(self):
        await self.async_api_command(self._attributes.stop_command(self._has_stop))

    async def async_set_position(self, value):
        if not self.is_slider:
            raise NotImplementedError

        await self.async_api_command("position", value)

    def _read_desired(self):
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        raw = self.raw_value("desired")
        min_position = self._attributes.min_position
        return self._product.expect_int(alias, raw, 100, min_position)

    # TODO: refactor
    def _read_state(self):
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        return self._attributes.read_state(alias, self.raw_value, self._product)

    def _read_has_stop(self):
        return self._attributes.read_has_stop(
            self._alias, self.raw_value, self._product
        )

    def after_update(self):
        self._desired = self._read_desired()
        self._state = self._read_state()
        self._has_stop = self._read_has_stop()
