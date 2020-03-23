from .error import DeviceStateNotAvailable


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
            # TODO: coverage
            raise DeviceStateNotAvailable

        methods = self._methods
        return product.follow(product.last_data, methods[name])

    async def async_api_command(self, *args, **kwargs):
        await self._product.async_api_command(*args, **kwargs)
