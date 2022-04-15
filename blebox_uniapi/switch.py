from .feature import Feature
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from .box import Box


class Switch(Feature):
    _is_on: Optional[bool]

    def __init__(
        self,
        product: "Box",
        alias: str,
        methods: dict,
        dev_class: str,
        unit_id: Optional[str] = None,
    ):
        super().__init__(product, alias, methods)
        self._device_class = dev_class
        self._unit_id = unit_id

    def after_update(self) -> None:
        self._is_on = self._read_is_on()

    def _read_is_on(self) -> Optional[bool]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("state")
            if raw is not None:  # no reading
                alias = self._alias
                return 1 == product.expect_int(alias, raw, 1, 0)
        return None

    @property
    def is_on(self) -> Optional[bool]:
        return self._is_on

    @property
    def _unit_args(self) -> list:
        unit = self._unit_id
        return [] if unit is None else [unit]

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_api_command("on", *self._unit_args)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_api_command("off", *self._unit_args)
