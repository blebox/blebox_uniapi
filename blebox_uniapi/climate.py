from .sensor import Temperature
from .error import JPathFailed
from typing import Optional, Any, Union


class Climate(Temperature):
    _is_on: Optional[bool]
    _desired: Union[float, int, None]
    _is_heating: Optional[bool]
    _min_temp: Union[float, int, None]
    _max_temp: Union[float, int, None]

    @property
    def is_on(self) -> Optional[bool]:
        return self._is_on

    @property
    def desired(self) -> Any:
        return self._desired

    @property
    def current(self) -> Any:
        return self._current

    @property
    def max_temp(self) -> Union[float, int, None]:
        return self._max_temp

    @property
    def min_temp(self) -> Union[float, int, None]:
        return self._min_temp

    @property
    def is_heating(self) -> Optional[bool]:
        return self._is_heating

    async def async_on(self) -> None:
        await self.async_api_command("on")

    async def async_off(self) -> None:
        await self.async_api_command("off")

    async def async_set_temperature(self, value: Any) -> None:
        await self.async_api_command("set", int(round(value * 100.0)))

    def _read_is_on(self) -> Optional[bool]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("state")
            if raw is not None:  # no reading
                alias = self._alias
                return 1 == product.expect_int(alias, raw, 1, 0)
        return None

    def _read_is_heating(self) -> Optional[bool]:
        if not self._product.last_data:
            return None

        return self.is_on and (self.current < self.desired)

    def after_update(self) -> None:
        self._is_on = self._read_is_on()
        self._desired = self._read_temperature("desired")
        self._current = self._read_temperature("temperature")
        self._is_heating = self._read_is_heating()

        if self._product.last_data is None:
            self._min_temp = None
            self._max_temp = None
            return

        try:
            self.raw_value("minimum")
        except JPathFailed:
            # TODO: coverage
            return

        self._min_temp = self._read_temperature("minimum")
        self._max_temp = self._read_temperature("maximum")
