from .feature import Feature


class AirQuality(Feature):
    def __init__(self, product, alias, methods):
        super().__init__(product, alias, methods)

    @property
    def pm1(self):
        return self._pm1

    @property
    def pm2_5(self):
        return self._pm2_5

    @property
    def pm10(self):
        return self._pm10

    def _pm_value(self, name):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(name)
            if raw is not None:  # no reading
                alias = self._alias
                return product.expect_int(alias, raw, 3000, 0)
        return None

    def after_update(self):
        self._pm1 = self._pm_value("pm1.value")
        self._pm2_5 = self._pm_value("pm2_5.value")
        self._pm10 = self._pm_value("pm10.value")
