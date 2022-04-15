from .feature import Feature
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .box import Box


class AirQuality(Feature):
    _pm1: Optional[int]
    _pm2_5: Optional[int]
    _pm10: Optional[int]

    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)

    @property
    def pm1(self) -> Optional[int]:
        return self._pm1

    @property
    def pm2_5(self) -> Optional[int]:
        return self._pm2_5

    @property
    def pm10(self) -> Optional[int]:
        return self._pm10

    def _pm_value(self, name: str) -> Optional[int]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(name)
            if raw is not None:  # no reading
                alias = self._alias
                return product.expect_int(alias, raw, 3000, 0)
        return None

    def after_update(self) -> None:
        self._pm1 = self._pm_value("pm1.value")
        self._pm2_5 = self._pm_value("pm2_5.value")
        self._pm10 = self._pm_value("pm10.value")
