from .sensor import Temperature


class Climate(Temperature):
    @property
    def is_on(self):
        return self._is_on

    @property
    def desired(self):
        return self._desired

    @property
    def current(self):
        return self._current

    @property
    def is_heating(self):
        return self._is_heating

    async def async_on(self):
        await self.async_api_command("on")

    async def async_off(self):
        await self.async_api_command("off")

    async def async_set_temperature(self, value):
        await self.async_api_command("set", int(round(value * 100.0)))

    def _read_is_on(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("state")
            if raw is not None:  # no reading
                alias = self._alias
                return 1 == product.expect_int(alias, raw, 1, 0)
        return None

    def _read_is_heating(self):
        if not self._product.last_data:
            return None

        return self.is_on and (self.current < self.desired)

    def after_update(self):
        self._is_on = self._read_is_on()
        self._desired = self._read_temperature("desired")
        self._current = self._read_temperature("temperature")
        self._is_heating = self._read_is_heating()
