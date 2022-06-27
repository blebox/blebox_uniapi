from .feature import Feature
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .box import Box


class Sensor(Feature):
    _unit: str

    def __init__(self, product: "Box", alias: str, methods: dict):
        super.__init__(product, alias, methods)

    @property
    def unit(self) -> str:
        return self._unit

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state) -> list["Sensor"]:
        pass
        sensor_list = list()
        print("SENSOR many from config.:",len(box_type_config[0]))
        alias, methods = box_type_config[0]
        if extended_state is not None:
            print("SENSOR mfc ex state")
        return [Temperature(product=product, alias=alias, methods=methods)]


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


class Wind(Sensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        self._unit = "m/s"
        self._device_class = "temperature"
        super().__init__(product, alias, methods)


class Rain(Sensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        self._device_class = "moisture"
        super().__init__(product, alias, methods)
    @property
    def state(self) -> bool:
        return True

    @property
    def device_class(self) -> str:
        return self._device_class



# todo Implement new many_from_host basing on extended state(each class initialising basing on: for each sensor in sensors: type:---
# to set device_class, native_unit_of_measurment, state class
