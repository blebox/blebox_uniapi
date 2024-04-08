import datetime
import numbers
from functools import partial

from .feature import Feature
from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from .box import Box


class SensorFactory:
    type_class_mapper: dict[str, type] = {}

    @classmethod
    def register(cls, sensor_type: str, **kwargs):
        if sensor_type in cls.type_class_mapper:
            raise RuntimeError("Can't register same sensor type twice")

        def decorator(registrable: type):
            if kwargs:
                registrable = partial(registrable, **kwargs)

            cls.type_class_mapper[sensor_type] = registrable
            return registrable

        return decorator

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state):
        type_class_mapper = cls.type_class_mapper

        if extended_state:
            object_list = []
            alias, methods = box_type_config[0]
            sensor_list = extended_state.get("multiSensor", {}).get("sensors", [])

            for sensor in sensor_list:
                device_class = sensor.get("type")
                sensor_id = sensor.get("id")

                if type_class_mapper.get(device_class):
                    value_method = {device_class: methods[device_class](sensor_id)}
                    object_list.append(
                        type_class_mapper[device_class](
                            product=product,
                            alias=f"{device_class}_{str(sensor_id)}",
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

    def __init__(self, product: "Box", alias: str, methods: dict, sensor_type: str = None):
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


# todo: proxu device class in all sensor inits
@SensorFactory.register("frequency", unit="Hz", scale=1_000)
@SensorFactory.register("current", unit="mA", scale=10)
@SensorFactory.register("voltage", unit="V", scale=10)
@SensorFactory.register("apparentPower", unit="va",)
@SensorFactory.register("reactivePower", unit="var")
@SensorFactory.register("activePower", unit="W")
@SensorFactory.register("reverseActiveEnergy", unit="kWh")
@SensorFactory.register("forwardActiveEnergy", unit="kWh")
@SensorFactory.register("illuminance", unit="lx", scale=100)
@SensorFactory.register("humidity", unit="percentage", scale=100)
class GenericSensor(BaseSensor):
    def __init__(
        # base sensor params
        self, product: "Box", alias: str, methods: dict, *,
        # generalization params
        sensor_type: str,
        unit: str,
        scale: float = 1,
        precision: int | None = None
    ):
        super().__init__(product, alias, methods)
        self._device_class = sensor_type
        self._unit = unit
        self._scale = scale
        self._precision = precision

    @property
    def after_update(self):
        product = self._product
        if product.last_data is None:
            return

        raw = self.raw_value(self._device_class)
        if not isinstance(raw, numbers.Number):
            raw = float("nan")

        native = raw / self._scale
        if self._precision:
            native = round(native, self._precision)

        self._native_value = native


# deprecated
# TODO: add some deprecation utilities
@SensorFactory.register("wind", scale=10)
class Wind(GenericSensor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # the only difference from real generic sensor is device_class value
        # todo: check if it can be updated upstream
        self._device_class = "wind_speed"


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
