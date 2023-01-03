from .error import DeviceStateNotAvailable
from typing import Any, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .box import Box


class Feature:
    _device_class: str

    def __init__(self, product: "Box", alias: str, methods: dict):
        self._product = product
        self._alias = alias
        self._methods = methods

    @classmethod
    def many_from_config(
        cls, product, box_type_config, extended_state
    ) -> list["Feature"]:
        # note: by default single config entry yields single feature instance but certain feature
        # domains (e.g. lights) may handle this differently depending on their `extended_state`
        return [cls(product, *args) for args in box_type_config]

    @property
    def unique_id(self) -> str:
        return f"BleBox-{self._product.type}-{self._product.unique_id}-{self._alias}"

    async def async_update(self) -> None:
        await self._product.async_update_data()

    @property
    def full_name(self) -> str:
        product = self._product
        return f"{product.name} ({product.type}#{self._alias})"

    @property
    def device_class(self) -> str:
        return self._device_class

    @property
    def product(self) -> "Box":
        return self._product

    # TODO: (cleanup) move to product/box ?
    def raw_value(self, name: str) -> Any:
        product = self._product
        # TODO: better exception?
        if product.last_data is None:
            # TODO: coverage
            raise DeviceStateNotAvailable  # pragma: no cover
        methods = self._methods
        if method := methods.get(name):
            return product.follow(product.last_data, method)
        return None

    async def async_api_command(self, *args: Any, **kwargs: Any) -> None:
        await self._product.async_api_command(*args, **kwargs)

    @staticmethod
    def resolve_access_method_paths(
        methods: dict[str, Union[str, callable]], id_val: str = None
    ) -> dict[str, str]:
        """Return dict with resolved callable used as data path."""
        new = dict()
        if not isinstance(methods, dict):
            raise TypeError(
                f"Parameter methods should be dict, instead of {type(methods)}."
            )
        for key, value in methods.items():
            if callable(value):
                new[key] = value(id_val)
            else:
                new[key] = value
        return new
