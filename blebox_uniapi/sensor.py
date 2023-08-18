import datetime

from .feature import Feature
from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from .box import Box


class BaseSensor(Feature):
    _unit: str
    _device_class: str
    _native_value: Union[float, int, str]

    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def device_class(self) -> str:
        return self._device_class

    @property
    def native_value(self):
        return self._native_value

    def many_from_config(cls, product, box_type_config, extended_state):
        raise NotImplementedError("Please use SensorFactory")


class Temperature(BaseSensor):
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
            if raw is not None:
                alias = self._alias
                # 12500, -5500 is a representation of temperature range in millidegree Celsius
                return round(product.expect_int(alias, raw, 12500, -5500) / 100.0, 1)
        return None

    def after_update(self) -> None:
        self._current = self._read_temperature("temperature")
        self._native_value = self._read_temperature("temperature")


class AirQuality(BaseSensor):
    _pm: Optional[int]

    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "concentration_of_mp"
        self._device_class = alias

    def _pm_value(self, name: str) -> Optional[int]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(name)
            if raw is not None:
                alias = self._alias
                return product.expect_int(alias, raw, 3000, 0)
        return None

    def after_update(self) -> None:
        self._native_value = self._pm_value(f"{self.device_class}.value")


class Humidity(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "percentage"
        self._device_class = "humidity"

    def _read_humidity(self, field: str) -> Optional[int]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(field)
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 10000, 0) / 100.0, 1)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_humidity(f"{self.device_class}")


class Energy(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "kWh"
        self._device_class = "powerMeasurement"

    @property
    def last_reset(self):
        return datetime.datetime.now() - datetime.timedelta(
            seconds=self._read_period_of_measurement()
        )

    def _read_period_of_measurement(self) -> int:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("periodS")
            if raw is not None:
                alias = self._alias
                return product.expect_int(alias, raw, 3600, 0)
        return 0

    def _read_power_measurement(self):
        product = self._product
        if product.last_data is not None:
            raw = float(self.raw_value("energy"))
            return raw
        return None

    def after_update(self) -> None:
        self._native_value = self._read_power_measurement()


class Wind(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "m/s"
        self._device_class = "wind_speed"

    def _read_wind_speed(self):
        product = self._product
        if product.last_data is not None:
            return self.raw_value("wind")

    def after_update(self) -> None:
        self._native_value = self._read_wind_speed()


class SensorFactory:
    @classmethod
    def many_from_config(
        cls, product, box_type_config, extended_state
    ) -> list["BaseSensor"]:
        type_class_mapper = {
            "airSensor": AirQuality,
            "temperature": Temperature,
            "humidity": Humidity,
            "wind": Wind,
        }
        if extended_state:
            object_list = list()
            alias, methods = box_type_config[0]
            sensor_list = extended_state.get("multiSensor", {}).get("sensors", [])
            for sensor in sensor_list:
                sensor_type = sensor.get("type")
                sensor_id = sensor.get("id")
                if type_class_mapper.get(sensor_type):
                    value_method = {sensor_type: methods[sensor_type](sensor_id)}
                    object_list.append(
                        type_class_mapper[sensor_type](
                            product=product,
                            alias=f"{sensor_type}_{str(sensor_id)}",
                            methods=value_method,
                        )
                    )
            ### power consumption
            if "powerConsumption" in str(extended_state):
                consumption_meters = extended_state.get("powerMeasuring", {}).get(
                    "powerConsumption", []
                )
                for _ in consumption_meters:
                    # method = methods
                    object_list.append(
                        Energy(
                            product=product, alias="powerConsumption", methods=methods
                        )
                    )

            return object_list
        else:
            alias, methods = box_type_config[0]
            if alias.endswith("air"):
                method_list = [method for method in methods if "value" in method]
                return [
                    AirQuality(
                        product=product, alias=method.split(".")[0], methods=methods
                    )
                    for method in method_list
                ]
            if alias.endswith("temperature"):
                return [Temperature(product=product, alias=alias, methods=methods)]
            else:
                return []
