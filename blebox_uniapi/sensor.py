import datetime
from enum import IntEnum
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
                    materialized_methods = Feature.resolve_access_method_paths(
                        methods, sensor_id
                    )

                    feature = constructor(
                        product=product,
                        alias=alias,
                        methods=materialized_methods,
                        sensor_id=sensor_id,
                        name=sensor.get("name"),
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


class BleboxSensorState(IntEnum):
    """Possible states of a sensor reading, not all valid for every device type."""

    IDLE = 0
    INITIALIZING = 1
    ACTIVE = 2
    ERROR = 3
    ABOVE_RANGE = 4
    BELOW_RANGE = 5


class BaseSensor(Feature):
    _unit: str
    _device_class: str
    _native_value: Optional[Union[float, int, str]] = None
    _sensor_type: Optional[str]
    _sensor_id: Optional[int]
    _error: bool = False

    def __init__(
        self,
        product: "Box",
        alias: str,
        methods: dict,
        sensor_type: str = None,
        sensor_id: Optional[int] = None,
        name: Optional[str] = None,
    ):
        self._sensor_type = sensor_type
        self._sensor_id = sensor_id
        self._name = name
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

    @property
    def is_error(self) -> bool:
        return self._error

    def _read_state(self, name: str) -> Optional[int]:
        if self._product.last_data is None:
            return None
        raw = self.raw_value(f"{name}.state")
        if not isinstance(raw, (int, float)):
            return None
        return int(raw)

    @staticmethod
    def _state_is_error(state: Optional[int]) -> bool:
        return state == BleboxSensorState.ERROR

    @staticmethod
    def _state_is_initializing(state: Optional[int]) -> bool:
        return state == BleboxSensorState.INITIALIZING

    @property
    def sensor_id(self):
        return self._sensor_id

    @property
    def probe_id(self):
        return self.sensor_id

    @property
    def index(self) -> Optional[int]:
        return self._sensor_id

    @property
    def name(self) -> Optional[str]:
        return self._name

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state):
        raise NotImplementedError("Please use SensorFactory")

    def __str__(self):
        return f"<{self.__class__.__name__} sensor_type={self._sensor_type}, alias={self._alias}>"


@SensorFactory.register("frequency", unit="Hz", scale=1_000)
@SensorFactory.register("current", unit="mA")
@SensorFactory.register("voltage", unit="V", scale=10)
@SensorFactory.register("apparentPower", unit="va")
@SensorFactory.register("reactivePower", unit="var")
@SensorFactory.register("activePower", unit="W")
@SensorFactory.register("reverseReactiveEnergy", unit="kvarh", scale=1_000)
@SensorFactory.register("forwardReactiveEnergy", unit="kvarh", scale=1_000)
@SensorFactory.register("reverseActiveEnergy", unit="kWh", scale=1_000)
@SensorFactory.register("forwardActiveEnergy", unit="kWh", scale=1_000)
@SensorFactory.register("illuminance", unit="lx", scale=100)
@SensorFactory.register("humidity", unit="percentage", scale=100)
@SensorFactory.register("wind", unit="m/s", scale=10)
@SensorFactory.register("openStatus", unit="")
@SensorFactory.register("co2", unit="ppm")
@SensorFactory.register("co2Definition", unit="")
class GenericSensor(BaseSensor):
    def __init__(
        # base sensor params
        self,
        product: "Box",
        alias: str,
        methods: dict,
        sensor_id: Optional[int],
        name: Optional[str] = None,
        *,
        # generalization params
        sensor_type: str,
        unit: str,
        scale: float = 1,
        precision: Optional[int] = None,
    ):
        super().__init__(product, alias, methods, sensor_id=sensor_id, name=name)
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

        state = self._read_state(self._device_class)
        if self._state_is_error(state):
            self._error = True
            self._native_value = None
            return

        self._error = False

        if self._state_is_initializing(state):
            self._native_value = None
            return

        raw = self.raw_value(self._device_class)
        if not isinstance(raw, (int, float)):
            self._native_value = None
            return

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
    _current: Optional[Union[float, int]]

    def __init__(
        self,
        product: "Box",
        alias: str,
        methods: dict,
        sensor_id: Optional[int] = None,
        name: Optional[str] = None,
    ):
        super().__init__(product, alias, methods, sensor_id=sensor_id, name=name)
        self._unit = "celsius"
        self._device_class = "temperature"

    @property
    def current(self) -> Optional[Union[float, int]]:
        return self._current

    def _read_temperature(self, field: str) -> Optional[Union[float, int]]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(field)
            if isinstance(raw, (int, float)):
                return round(raw / 100.0, 1)
        return None

    def after_update(self) -> None:
        state = self._read_state("temperature")
        if self._state_is_error(state):
            self._error = True
            self._current = None
            self._native_value = None
            return

        self._error = False

        if self._state_is_initializing(state):
            self._current = None
            self._native_value = None
            return

        current = self._read_temperature("temperature")
        self._current = current
        self._native_value = current


@SensorFactory.register("airSensor")
class AirQuality(BaseSensor):
    _pm: Optional[int]

    def __init__(
        self,
        product: "Box",
        alias: str,
        methods: dict,
        sensor_id: Optional[str] = None,
        name: Optional[str] = None,
    ):
        super().__init__(product, alias, methods, sensor_id, name=name)
        self._unit = "concentration_of_mp"
        self._device_class = alias

    def _pm_value(self, name: str) -> Optional[Union[int, float]]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(name)
            if isinstance(raw, (int, float)):
                return raw
        return None

    def after_update(self) -> None:
        state = self._read_state(self.device_class)
        if self._state_is_error(state):
            self._error = True
            self._native_value = None
            return

        self._error = False

        if self._state_is_initializing(state):
            self._native_value = None
            return

        self._native_value = self._pm_value(f"{self.device_class}.value")
