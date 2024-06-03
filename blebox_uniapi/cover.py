from enum import IntEnum, auto

from .error import MisconfiguredDevice
from .feature import Feature
from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar

if TYPE_CHECKING:
    from .box import Box


class BleboxCoverState(IntEnum):
    """BleboxCoverState defines possible states of cover devices.

    Note that enumeration of states is partially shared between
    different types of devices (shutterBox, gateController) but
    not all states are possible for every type. For details of
    states refer to blebox official API documentation.
    """

    MOVING_DOWN = 0
    MOVING_UP = 1
    MANUALLY_STOPPED = 2
    LOWER_LIMIT_REACHED = 3
    UPPER_LIMIT_REACHED = 4
    OVERLOAD = 5
    MOTOR_FAILURE = 6
    UNUSED = 7
    SAFETY_STOP = 8


class ShutterBoxControlType(IntEnum):
    """ShutterBoxControlType defines shuterBox command semantics"""

    SEGMENTED_SHUTTER = 1
    NO_CALIBRATION = 2
    TILT_SHUTTER = 3
    WINDOW_OPENER = 4
    MATERIAL_SHUTTER = 5
    AWNING = 6
    SCREEN = 7
    CURTAIN = 8


class GateBoxControlType(IntEnum):
    """GateBoxControlType defines gateBox command semantics known as `openCloseMode`.

    Control type affects mainly [o]pen, [c]lose, and [n]ext commands which
    are wrappers around [p]rimary and [s]econdary outputs. The only exception
    is OPEN_CLOSE (2) control type that also means that the gateBox lacks
    stop action because typical stop output is wired to [c]lose/[s]econdary
    command.
    """

    STEP_BY_STEP = 0
    ONLY_OPEN = 1
    OPEN_CLOSE = 2


class GateBoxGateType(IntEnum):
    """GateBoxGateType defines possible gate/cover types reported by gateBox"""

    SLIDING_DOOR = 0
    GARAGE_DOOR = 1
    OVER_DOOR = 2
    DOOR = 3


class UnifiedCoverType(IntEnum):
    """UnifiedCoverType defines single "cover type" concept shared between different
    devices.

    Some device types have concept of control type/mode that affects how device
    operates and how it is being used (e.g. control type in shutterBox/gateControler),
    but others have these two concepts separated (e.g. open mode vs. gate type in
    gateBox). This enum provides unified concept of controlled cover type that
    can be infered from internal device information end exposed to library user.

    """

    AWNING = auto()
    BLIND = auto()
    CURTAIN = auto()
    DAMPER = auto()
    DOOR = auto()
    GARAGE = auto()
    GATE = auto()
    SHADE = auto()
    SHUTTER = auto()
    WINDOW = auto()


class Gate:
    _control_type: Optional[int]

    def __init__(self, control_type: int):
        self._control_type = control_type

    def read_state(self, alias: str, raw_value: Any, product: "Box") -> int:
        raw = raw_value("state")
        return product.expect_int(alias, raw, max(BleboxCoverState).value, 0)

    def read_desired(self, alias: str, raw_value: Any, product: "Box") -> Optional[int]:
        raw = raw_value("desired")
        min_position = self.min_position
        return product.expect_int(alias, raw, 100, min_position)

    def read_tilt(self, alias: str, raw_value: Any, product: "Box") -> int:
        raw = raw_value("tilt")
        min_position = self.min_position
        return product.expect_int(alias, raw, 100, min_position)

    def read_cover_type(
        self, alias: str, raw_value: Any, product: "Box"
    ) -> UnifiedCoverType:
        return UnifiedCoverType.GATE

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
    _control_type: Optional[ShutterBoxControlType]

    @property
    def min_position(self) -> int:
        return -1  # "unknown"

    @property
    def has_tilt(self) -> bool:
        return self._control_type == ShutterBoxControlType.TILT_SHUTTER

    def read_cover_type(
        self, alias: str, raw_value: Any, product: "Box"
    ) -> UnifiedCoverType:
        if self._control_type == ShutterBoxControlType.SEGMENTED_SHUTTER:
            return UnifiedCoverType.SHUTTER
        if self._control_type == ShutterBoxControlType.NO_CALIBRATION:
            return UnifiedCoverType.SHUTTER
        if self._control_type == ShutterBoxControlType.TILT_SHUTTER:
            return UnifiedCoverType.SHUTTER
        if self._control_type == ShutterBoxControlType.WINDOW_OPENER:
            return UnifiedCoverType.WINDOW
        if self._control_type == ShutterBoxControlType.MATERIAL_SHUTTER:
            return UnifiedCoverType.SHADE
        if self._control_type == ShutterBoxControlType.AWNING:
            return UnifiedCoverType.AWNING
        if self._control_type == ShutterBoxControlType.SCREEN:
            return UnifiedCoverType.SHADE
        if self._control_type == ShutterBoxControlType.CURTAIN:
            return UnifiedCoverType.CURTAIN


class GateBox(Gate):
    _control_type: Optional[GateBoxControlType]

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

        button_type = raw_value("extraButtonType")
        if button_type is None:
            return False

        return button_type == 1


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
        return raw_value("position")

    def read_has_stop(self, alias: str, raw_value: Any, product: "Box") -> bool:
        # note: if control type is unknown we assume it is not open/close
        #       and has the stop feature via secondary button command.
        return self._control_type != GateBoxControlType.OPEN_CLOSE

    def read_cover_type(
        self, alias: str, raw_value: Any, product: "Box"
    ) -> Optional[UnifiedCoverType]:
        if (gate_type := raw_value("gate_type")) is None:
            return

        if gate_type == GateBoxGateType.GARAGE_DOOR:
            return UnifiedCoverType.GARAGE
        if gate_type == GateBoxGateType.SLIDING_DOOR:
            return UnifiedCoverType.GATE
        return UnifiedCoverType.DOOR

    @property
    def close_command(self) -> str:
        if self._control_type == GateBoxControlType.OPEN_CLOSE:
            return "secondary"

        return super().close_command


GateT = TypeVar("GateT", bound=Gate)


# TODO: handle tilt
class Cover(Feature):
    _desired: Optional[int]
    _state: Optional[BleboxCoverState]
    _has_stop: Optional[bool]
    _cover_type: Optional[UnifiedCoverType]

    def __init__(
        self,
        product: "Box",
        alias: str,
        methods: dict,
        dev_class: str,
        subclass: Type[GateT],
        extended_state: dict,
    ) -> None:
        control_type = None
        if extended_state and issubclass(subclass, Shutter):
            control_type = extended_state.get("shutter", {}).get("controlType", None)
        elif extended_state and issubclass(subclass, GateBoxB):
            control_type = extended_state.get("gate", {}).get("openCloseMode", None)

        self._device_class = dev_class
        self._attributes: GateT = subclass(control_type)
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

    @property
    def cover_type(self) -> Optional[UnifiedCoverType]:
        return self._cover_type

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
        if self.has_tilt:
            await self.async_api_command("tilt", value)
        else:
            raise NotImplementedError

    async def async_close_tilt(self, **kwargs: Any) -> None:
        await self.async_api_command("tilt", 100)

    async def async_open_tilt(self, **kwargs: Any) -> None:
        await self.async_api_command("tilt", 0)

    def _read_cover_type(self) -> Optional[UnifiedCoverType]:
        product = self._product
        if not product.last_data:
            return None

        alias = self._alias
        return self._attributes.read_cover_type(alias, self.raw_value, self._product)

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
        self._cover_type = self._read_cover_type()

        if self._attributes.has_tilt:
            self._tilt_current = self._read_tilt()
