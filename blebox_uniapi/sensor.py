import datetime
from .feature import Feature
from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from .box import Box


class SensorFactory:
    type_class_mapper: dict[str, type] = {}

    @classmethod
    def register(cls, sensor_type: str):
        def decorator(subclass: type):
            cls.type_class_mapper[sensor_type] = subclass
            return subclass

        return decorator

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state):
        type_class_mapper = cls.type_class_mapper
        if extended_state:
            object_list = []
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

            if "powerConsumption" in str(extended_state):
                consumption_meters = extended_state.get("powerMeasuring", {}).get(
                    "powerConsumption", []
                )
                for _ in consumption_meters:
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

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state):
        raise NotImplementedError("Please use SensorFactory")


@SensorFactory.register("frequency")
class Frequency(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "Hz"
        self._device_class = "frequency"

    def _read_frequency(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("frequency")
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 1000000, -100000)/1000.0, 2)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_frequency()
        self._current = self._read_frequency()


@SensorFactory.register("current")
class Current(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "mA"
        self._device_class = "current"

    def _read_current(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("current")
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 1000000, -100000)/1000, 2)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_current()
        self._current = self._read_current()


@SensorFactory.register("voltage")
class Voltage(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "v"
        self._device_class = "voltage"

    def _read_voltage(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("voltage")
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 1000000, -100000)/10.0, 2)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_voltage()
        self._current = self._read_voltage()


@SensorFactory.register("apparentPower")
class ApparentPower(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "va"
        self._device_class = "apparentPower"

    def _read_apparentPower(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("apparentPower")
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 1000000, -100000), 2)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_apparentPower()
        self._current = self._read_apparentPower()


@SensorFactory.register("reactivePower")
class ReactivePower(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "var"
        self._device_class = "reactivePower"

    def _read_reactivePower(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("reactivePower")
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 10000000, -100000000), 2)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_reactivePower()
        self._current = self._read_reactivePower()


@SensorFactory.register("activePower")
class ActivePower(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "W"
        self._device_class = "activePower"

    def _read_activePower(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("activePower")
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 10000000, -100000000), 1)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_activePower()
        self._current = self._read_activePower()


@SensorFactory.register("reverseActiveEnergy")
class ReverseActiveEnergy(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "kWh"
        self._device_class = "reverseActiveEnergy"

    def _read_reverseActiveEnergy(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("reverseActiveEnergy")
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 10000000, 0)/1000, 2)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_reverseActiveEnergy()
        self._current = self._read_reverseActiveEnergy()


@SensorFactory.register("forwardActiveEnergy")
class ForwardActiveEnergy(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "kWh"
        self._device_class = "forwardActiveEnergy"

    def _read_forwardActiveEnergy(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("forwardActiveEnergy")
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 10000000, 0)/1000, 2)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_forwardActiveEnergy()
        self._current = self._read_forwardActiveEnergy()


@SensorFactory.register("illuminance")
class Illuminance(BaseSensor):
    _current: Union[float, int, None]

    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "lx"
        self._device_class = "illuminance"

    @property
    def current(self) -> Union[float, int, None]:
        return self._current

    def _read_illuminance(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("illuminance")
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 10000000, 0) / 100.0, 1)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_illuminance()
        self._current = self._read_illuminance()


@SensorFactory.register("temperature")
class Temperature(BaseSensor):
    _current: Union[float, int, None]

    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "celsius"
        self._device_class = "temperature"

    @property
    def current(self) -> Union[float, int, None]:
        return self._current

    def _read_temperature(self, field: str) -> Union[float, int, None]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(field)
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 12500, -5500) / 100.0, 1)
        return None

    def after_update(self) -> None:
        self._current = self._read_temperature("temperature")
        self._native_value = self._read_temperature("temperature")


@SensorFactory.register("airSensor")
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


@SensorFactory.register("humidity")
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


@SensorFactory.register("wind")
class Wind(BaseSensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "m/s"
        self._device_class = "wind_speed"

    def _read_wind_speed(self):
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("wind")
            if raw is not None:
                alias = self._alias
                # wind value unit in API is "0.1 m/s" so to get m/s we need to divide by 10
                # min value = 0, max value for sure not bigger than 200km/h so about 60m/s so 600 in API
                return round(product.expect_int(alias, raw, 600, 0) / 10.0, 1)
        return None

    def after_update(self) -> None:
        self._native_value = self._read_wind_speed()
