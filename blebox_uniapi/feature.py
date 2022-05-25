from .error import DeviceStateNotAvailable
from typing import Any, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .box import Box


class Feature:
    _device_class: str

    def __init__(self, product: "Box", alias: str, methods: dict):
        self._product = product
        self._alias = alias
        self._methods = methods

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
        # print(f"last data: {product.last_data}\nmethods:{methods}")
        if methods.get(name, None) is not None:
            return product.follow(product.last_data, methods[name])
        return None

    async def async_api_command(self, *args: Any, **kwargs: Any) -> None:

        await self._product.async_api_command(*args, **kwargs)
