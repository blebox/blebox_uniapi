from .feature import Feature


class Sensor(Feature):
    @property
    def unit(self):
        return self._unit


class Temperature(Sensor):
    def __init__(self, product, alias, methods):
        self._unit = "celsius"
        self._device_class = "temperature"
        super().__init__(product, alias, methods)

    @property
    def current(self):
        return self._current

    # TODO: use as attribute in product config
    def _read_temperature(self, field):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(field)
            if raw is not None:  # no reading
                alias = self._alias
                return round(product.expect_int(alias, raw, 12500, -5500) / 100.0, 1)
        return None

    def after_update(self):
        self._current = self._read_temperature("temperature")
