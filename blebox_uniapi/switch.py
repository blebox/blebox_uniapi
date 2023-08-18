from .feature import Feature
from typing import TYPE_CHECKING, Optional, Any, Union

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
        unit_id: Union[str, int, None] = 0,
    ):
        methods = self.resolve_access_method_paths(methods, str(unit_id))
        super().__init__(product, alias, methods)
        self._device_class = dev_class
        self._unit_id = unit_id

    @classmethod
    def many_from_config(
        cls, product, box_type_config, extended_state
    ) -> list["Switch"]:
        """
        :param product: Object hosting device with specific feature.
        :param box_type_config: Default configuration providing following data
        [
            [feature_alias, {method_name: method_path_or_method_path_callable}, relay_type, unit_id]
        ]
        :param extended_state: Object hosting extended state recieved from device
        :return: List of class objects instances
        """
        if extended_state:
            relay_list = list()
            alias, methods, relay_type, *rest = box_type_config[0]
            for relay in extended_state.get("relays", []):
                relay_id = relay.get("relay")
                relay_list.append(
                    cls(
                        product,
                        alias + "_" + str(relay_id),
                        methods,
                        relay_type,
                        relay_id,
                    )
                )

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
