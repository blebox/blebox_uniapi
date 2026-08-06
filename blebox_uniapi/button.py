from .cover import GateBoxControlType, GateBoxExtraButtonType
from .feature import Feature
from typing import TYPE_CHECKING, Any, Optional, Type

from enum import Enum, auto

if TYPE_CHECKING:
    from .box import Box

TV_LIFT_CONTROL_TYPES_API = {
    0: {"1": "open_or_stop", "2": "close_or_stop"},
    1: {"1": "up_or_stop", "2": "down_or_stop"},
    2: {"1": "up_or_stop", "2": "down_or_stop"},
    3: {"1": "up_or_stop", "2": "down_or_stop"},
    4: {"1": "open_or_stop", "2": "close_or_stop", "3": "to_fav"},
}


class ControlType(Enum):
    UP = auto()
    DOWN = auto()
    FAVORITE = auto()
    OPEN = auto()
    CLOSE = auto()


class Buttons:
    """Buttons defines how a product derives its buttons from extended state."""

    @staticmethod
    def many_from_extended_state(
        button_cls: Type["Button"],
        product: "Box",
        alias: str,
        methods: dict,
        extended_state: dict,
    ) -> list["Button"]:
        raise NotImplementedError  # pragma: no cover


class TvLift(Buttons):
    @staticmethod
    def many_from_extended_state(
        button_cls: Type["Button"],
        product: "Box",
        alias: str,
        methods: dict,
        extended_state: dict,
    ) -> list["Button"]:
        control_type = extended_state.get("tvLift", {}).get("controlType")
        endpoints = TV_LIFT_CONTROL_TYPES_API.get(control_type, {})
        return [
            button_cls(product, f"{alias}_{endpoint}", methods, endpoint)
            for endpoint in endpoints.values()
        ]


class GateBoxSecondOutput(Buttons):
    """GateBoxSecondOutput exposes the gateBox extra button output as a button.

    WALK_IN and OTHER share one button name because what the output does is a
    device setting the user can change at any time, not a hardware trait.
    """

    @staticmethod
    def many_from_extended_state(
        button_cls: Type["Button"],
        product: "Box",
        alias: str,
        methods: dict,
        extended_state: dict,
    ) -> list["Button"]:
        gate = extended_state.get("gate", {})
        if gate.get("extraButtonType") not in (
            GateBoxExtraButtonType.WALK_IN,
            GateBoxExtraButtonType.OTHER,
        ):
            return []

        # Api levels below 20230102 report no mode and cannot be wired that way.
        if gate.get("openCloseMode") == GateBoxControlType.OPEN_CLOSE:
            return []

        return [button_cls(product, alias, methods, "second_output", "secondary")]


class Button(Feature):
    def __init__(
        self,
        product: "Box",
        alias: str,
        methods: dict,
        query_string: str,
        api_command: str = "set",
    ) -> None:
        super().__init__(product, alias, methods)
        self._device_class = "UPDATE"
        self._query_string: str = query_string
        self._api_command: str = api_command

    @classmethod
    def many_from_config(
        cls, product: "Box", box_type_config: list, extended_state: Any
    ) -> list["Button"]:
        if not isinstance(extended_state, dict):
            return []

        features: list[Button] = []
        for alias, methods, buttons in box_type_config:
            features.extend(
                buttons.many_from_extended_state(
                    cls, product, alias, methods, extended_state
                )
            )
        return features

    async def set(self) -> None:
        await self.async_api_command(self._api_command, self.query_string)

    def after_update(self) -> None:
        pass

    @property
    def control_type(self) -> Optional[ControlType]:
        """Return icon for endpoint."""
        if "up" in self.query_string:
            return ControlType.UP
        elif "down" in self.query_string:
            return ControlType.DOWN
        elif "fav" in self.query_string:
            return ControlType.FAVORITE
        elif "open" in self.query_string:
            return ControlType.OPEN
        elif "close" in self.query_string:
            return ControlType.CLOSE
        else:
            return None

    @property
    def query_string(self) -> str:
        return self._query_string
