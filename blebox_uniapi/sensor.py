import datetime
import numbers
from functools import partial

from .feature import Feature
from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from .box import Box


class SensorFactory:
    device_constructors: dict[str, type] = {}

    @classmethod
    def register(cls, sensor_type: str, **kwargs):
        if sensor_type in cls.device_constructors:
            raise RuntimeError("Can't register same sensor type twice")

        def decorator(registrable: type):
            constructor = registrable
            if kwargs:
                constructor = partial(registrable, sensor_type=sensor_type, **kwargs)

            cls.device_constructors[sensor_type] = constructor
            # note: returning unmodified, so we can register registrable
            # multiple times under different names and with different kwargs
            return registrable

        return decorator

    @staticmethod
    def _sensor_states(extended_state: dict):
        """Read potential sensor states from extended state dictionary"""
        # note: probably we should iterate extended state in future if there
        # are other api flavours other than multiSensor that provide sensors
        states = extended_state.get("multiSensor", {}).get("sensors", [])
        # note: but for now we are only able to support non-multisensor devices
        # that provide sensor data in extended data payload root
        states.extend(extended_state.get("sensors", []))
        # note: power measuring feature predates multiSensor API, so we need a small
        # shim to adapt older shape of power measuring schema to the new sensor API
        if "powerMeasuring" in extended_state:
            power_states = extended_state["powerMeasuring"].get("powerConsumption", [])
            # note: be careful of names as this has been historically named differently
            # in home-assistant
            states.extend({"type": "powerConsumption", **s} for s in power_states)
        return states

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state):
        if extended_state:
            object_list = []
            # note: first item was historically an alias, but it has been since
            # abandoned. We still keep it in the box config.
            _, methods = box_type_config[0]

            for sensor in cls._sensor_states(extended_state):
                device_class = sensor.get("type")
                sensor_id = sensor.get("id")

                alias = device_class
                if sensor_id is not None:
                    alias = f"{device_class}_{sensor_id}"

                if constructor := cls.device_constructors.get(device_class):
                    # note: methods for sensor readings are provided as template
                    # functions (lambdas) in the box config. We need to "materialize"
                    # them to make sure they are properly indexed by sensor ID
                    materialized_methods = {
                        **methods,
                        device_class: methods[device_class](sensor_id),
                    }

                    feature = constructor(
                        product=product, alias=alias, methods=materialized_methods
                    )
                    object_list.append(feature)

            return object_list

        # legacy handling of some old device API that do not provide extended state
        alias, methods = box_type_config[0]
        if alias.endswith("air"):
            method_list = [method for method in methods if "value" in method]
            return [
                AirQuality(product=product, alias=method.split(".")[0], methods=methods)
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
    _sensor_type: Optional[str]

    def __init__(
        self, product: "Box", alias: str, methods: dict, sensor_type: str = None
    ):
        self._sensor_type = sensor_type
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

    def __str__(self):
        return f"<{self.__class__.__name__} sensor_type={self._sensor_type}, alias={self._alias}>"


@SensorFactory.register("frequency", unit="Hz", scale=1_000)
@SensorFactory.register("current", unit="mA", scale=1_000)
@SensorFactory.register("voltage", unit="V", scale=10)
@SensorFactory.register("apparentPower", unit="va")
@SensorFactory.register("reactivePower", unit="var")
@SensorFactory.register("activePower", unit="W")
@SensorFactory.register("reverseActiveEnergy", unit="kWh")
@SensorFactory.register("forwardActiveEnergy", unit="kWh")
@SensorFactory.register("illuminance", unit="lx", scale=100)
@SensorFactory.register("humidity", unit="percentage", scale=100)
@SensorFactory.register("wind", unit="m/s", scale=10)
class GenericSensor(BaseSensor):
    def __init__(
        # base sensor params
        self,
        product: "Box",
        alias: str,
        methods: dict,
        *,
        # generalization params
        sensor_type: str,
        unit: str,
        scale: float = 1,
        precision: Optional[int] = None,
    ):
        super().__init__(product, alias, methods)
        self._unit = unit
        self._scale = scale
        self._precision = precision
        # note: this seems redundant but there is at least one sensor type that
        # has different mapping in home assistant (wind/wind_speed). Should be
        # fixed in upstream first.
        self._device_class = sensor_type
        self._sensor_type = sensor_type

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


@SensorFactory.register("powerConsumption", unit="kWh")
class PowerConsumption(GenericSensor):
    # note: almost the same as typical generic sensor but also provides extra property
    # to read last reset value
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
