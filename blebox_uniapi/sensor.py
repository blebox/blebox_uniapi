from .feature import Feature
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .box import Box


class Sensor(Feature):
    _unit: str

    @property
    def unit(self) -> str:
        return self._unit


class Temperature(Sensor):
    _current: Union[float, int, None]

    def __init__(self, product: "Box", alias: str, methods: dict):
        self._unit = "celsius"
        self._device_class = "temperature"
        super().__init__(product, alias, methods)

    @property
    def current(self) -> Union[float, int, None]:
        return self._current

    # TODO: use as attribute in product config
    def _read_temperature(self, field: str) -> Union[float, int, None]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(field)
            if raw is not None:  # no reading
                alias = self._alias
                return round(product.expect_int(alias, raw, 12500, -5500) / 100.0, 1)
        return None

    def after_update(self) -> None:
        self._current = self._read_temperature("temperature")
