from .error import JPathFailed
from .feature import Feature


class Sensor:

    def __init__(self, product, entities_data):
        self.product = product
        self.data = entities_data['multiSensor']['sensors']

    def create_entities(self):
        result = [self.create_entity(index=sensor_data['id'], name=sensor_data['type']) for sensor_data in self.data]
        return result

    def create_entity(self, index, name):
        entity_schemas = {
            'temperature': Temperature(
                product=self.product,
                alias=f'{index}.{name}',
                methods={
                    "temperature": f"multiSensor/sensors/[id={index}]/value",
                    "trend": f"multiSensor/sensors/[id={index}]/trend",
                    "state": f"multiSensor/sensors/[id={index}]/state",
                    "elapsed": f"multiSensor/sensors/[id={index}]/elapsedTimeS",
                }
            ),
            # add next types of sensors here
        }

        return entity_schemas[name]


class Temperature(Feature):
    def __init__(self, product, alias, methods):
        self._unit = "celsius"
        self._device_class = "temperature"
        super().__init__(product, alias, methods)

    @property
    def current(self):
        return self._current

    @property
    def unit(self):
        return self._unit

    # TODO: use as attribute in product config
    def _read_temperature(self, field):
        product = self._product
        if product.last_data is not None:
            # workaround for disabling/enabling some of the sensors
            try:
                raw = self.raw_value(field)
            except JPathFailed:
                return None

            if raw is not None:  # no reading
                alias = self._alias
                return round(product.expect_int(alias, raw, 12500, -5500) / 100.0, 1)

        return None

    def after_update(self):
        self._current = self._read_temperature("temperature")
