import blebox_uniapi.error
from .error import MisconfiguredDevice
from .feature import Feature
from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar

if TYPE_CHECKING:
    from .box import Box


class Gate:
    _control_type: int

    def __init__(self, control_type: int):
        self._control_type = control_type

    def read_state(self, alias: str, raw_value: Any, product: "Box") -> int:
        raw = raw_value("state")
        return product.expect_int(alias, raw, 4, 0)

    def read_desired(self, alias: str, raw_value: Any, product: "Box") -> Optional[int]:
        raw = raw_value("desired")
        min_position = self.min_position
        return product.expect_int(alias, raw, 100, min_position)

    def read_tilt(self, alias: str, raw_value: Any, product: "Box") -> int:
        raw = raw_value("tilt")
        min_position = self.min_position
        return product.expect_int(alias, raw, 100, min_position)

    @property
    def min_position(self) -> int:
        return 0

    @property
    def is_slider(self) -> bool:
        return True

    @property
    def has_tilt(self) -> bool:
        return False

    @property
    def open_command(self) -> str:
        return "open"

    @property
    def close_command(self) -> str:
        return "close"

    def stop_command(self, has_stop: bool) -> str:
        return "stop"

    def read_has_stop(self, alias: str, raw_value: Any, product: "Box") -> bool:
        return True


class Shutter(Gate):
    @property
    def min_position(self) -> int:
        return -1  # "unknown"

    @property
    def has_tilt(self) -> bool:
        if self._control_type == 3:
            return True
        return False


class GateBox(Gate):
    @property
    def is_slider(self) -> bool:
        return False

    @property
    def open_command(self) -> str:
        return "primary"

    @property
    def close_command(self) -> str:
        return "primary"

    def read_state(self, alias: str, raw_value: Any, product: "Box") -> int:
        # Reinterpret state to match shutterBox
        # NOTE: shutterBox is inverted (0 == closed), gateBox isn't
        current = raw_value("position")
        desired = raw_value("desired")

        # gate with gateBox visualized:
        #  (0) [   <#####] (100)
        if current == -1:
            return None

        if desired < current:
            return 0  # closing

        if desired > current:
            return 1  # opening

        if current == 0:  # closed
            return 3  # closed (lower/left limit)

        if current == 100:  # opened
            return 4  # open (upper/right limit)

        return 2  # manually stopped

    def stop_command(self, has_stop: bool) -> str:
        if not has_stop:
            raise MisconfiguredDevice("second button not configured as 'stop'")
        return "secondary"

    def read_has_stop(self, alias: str, raw_value: Any, product: "Box") -> bool:
        if product.last_data is None:
            return False
        try:
            raw = raw_value("extraButtonType")
        except blebox_uniapi.error.JPathFailed:
            return False
        return 1 == product.expect_int(alias, raw, 3, 0)


class GateBoxB(GateBox):
    def read_state(self, alias: str, raw_value: Any, product: "Box") -> int:
        current = raw_value("position")

        # gate with gateBox visualized:
        #  (0) [   <#####] (100)
        if current == -1:
            return None

        elif 0 < current < 100:
            return 2  # manually stopped
        elif current == 0:  # closed
            return 3  # closed (lower/left limit)

        return 4  # open (upper/right limit)

    def read_desired(self, alias: str, raw_value: Any, product: "Box") -> Optional[int]:
        return None

    def read_has_stop(self, alias: str, raw_value: Any, product: "Box") -> bool:
        """
        "extraButtonType" field isn't available in responses
        from "GET" posts to "/s/p" or "/s/s" so I just returned True
        """
        return True


GateT = TypeVar("GateT", bound=Gate)


# TODO: handle tilt
class Cover(Feature):
    def __init__(
        self,
        product: "Box",
        alias: str,
        methods: dict,
        dev_class: str,
        subclass: Type[GateT],
        extended_state: dict,
    ) -> None:

        self._control_type = None
        if extended_state not in [None, {}]:
            self._control_type = extended_state.get("shutter", {}).get(
                "controlType", {}
            )

        self._device_class = dev_class
        self._attributes: GateT = subclass(self._control_type)
        self._tilt_current = None
        super().__init__(product, alias, methods)

    @classmethod
    def many_from_config(
        cls, product, box_type_config, extended_state
    ) -> list["Feature"]:

        return [cls(product, *args, extended_state) for args in box_type_config]

    @property
    def current(self) -> Any:
        return self._desired

    @property
    def state(self) -> Any:
        return self._state

    @property
    def tilt_current(self):
        return self._tilt_current

    @property
    def is_slider(self) -> Any:
        return self._attributes.is_slider

    @property
    def has_tilt(self) -> bool:
        return self._attributes.has_tilt

    @property
    def has_stop(self) -> bool:
        return self._has_stop

    async def async_open(self) -> None:
        await self.async_api_command(self._attributes.open_command)

    async def async_close(self) -> None:
        await self.async_api_command(self._attributes.close_command)

    async def async_stop(self) -> None:
        await self.async_api_command(self._attributes.stop_command(self._has_stop))

    async def async_set_position(self, value: Any) -> None:
        if not self.is_slider:
            raise NotImplementedError

        await self.async_api_command("position", value)

    async def async_set_tilt_position(self, value: Any) -> None:
        if self.has_tilt and self._control_type == 3:
            await self.async_api_command("tilt", value)
        else:
            raise NotImplementedError

    def _read_desired(self) -> Any:
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        return self._attributes.read_desired(alias, self.raw_value, self._product)

    # TODO: refactor
    def _read_state(self) -> Any:
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        return self._attributes.read_state(alias, self.raw_value, self._product)

    def _read_tilt(self) -> Any:
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        return self._attributes.read_tilt(alias, self.raw_value, self._product)

    def _read_has_stop(self) -> bool:
        return self._attributes.read_has_stop(
            self._alias, self.raw_value, self._product
        )

    def after_update(self) -> None:
        self._desired = self._read_desired()
        self._state = self._read_state()
        self._has_stop = self._read_has_stop()
        if self._control_type == 3 and self._attributes.has_tilt:
            self._tilt_current = self._read_tilt()
