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

    @classmethod
    def many_from_config(
        cls, product, box_type_config, extended_state
    ) -> list["Feature"]:
        relay_list = list()
        if extended_state:
            alias, methods, relay_type, *_ = box_type_config[0]
            relays_in_ex = extended_state.get("relays", [])
            for relay in relays_in_ex:
                relay_id = relay.get("relay")
                value_method = Feature.access_method_path_resolver(methods, str(relay_id))
                relay_list.append(cls(product, alias+"_"+str(relay_id), value_method, relay_type, relay_id))
            return relay_list
        else:
            return [cls(product, *args) for args in box_type_config]

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
