from .feature import Feature


class Switch(Feature):
    def __init__(self, product, alias, methods, dev_class, unit_id=None):
        super().__init__(product, alias, methods)
        self._device_class = dev_class
        self._unit_id = unit_id

    def after_update(self):
        self._is_on = self._read_is_on()

    def _read_is_on(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("state")
            if raw is not None:  # no reading
                alias = self._alias
                return 1 == product.expect_int(alias, raw, 1, 0)
        return None

    @property
    def is_on(self):
        return self._is_on

    @property
    def _unit_args(self):
        unit = self._unit_id
        return [] if unit is None else [unit]

    async def async_turn_on(self, **kwargs):
        await self.async_api_command("on", *self._unit_args)

    async def async_turn_off(self, **kwargs):
        await self.async_api_command("off", *self._unit_args)
