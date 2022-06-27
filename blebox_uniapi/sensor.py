from .feature import Feature
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .box import Box


class Sensor(Feature):
    _unit: str

    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)

    @property
    def unit(self) -> str:
        return self._unit

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state) -> list["Sensor"]:
        #pass
        sensor_list = list()
        type_class_mapper = {
            "temperature": Temperature,
            "wind": Wind,
        }
        # robiera listę sensorów, wydziela im methods w zalezności o
        # utworzyc liste sensorów na podstawie extended state,
        # powinien implementodwać odpowiednią klasę dla danego typu urządenia,
        # modyfikować methods aby utrzymywać id obiektu(methods to path po drzewie do wartosci)

        print("SENSOR many from config.:",len(box_type_config[0]))
        alias, methods = box_type_config[0]
        print("Alias:",alias,"\nmethods:", methods,"\nES", extended_state)
        sensor_list = extended_state.get("multiSensor").get("sensors", {})
        print("\nsensor_list",sensor_list)
        s_li = list()
        for sensor in sensor_list:
            print("sensor:",sensor)
            sensor_type = sensor.get("type")
            sensor_id = sensor.get("id")
            value_method = {sensor_type: methods[sensor_type](sensor_id)}
            print("Sensor:", sensor_type, sensor_id, value_method)

            s_li.append(type_class_mapper[sensor_type](product=product, alias=sensor_type + "_" + str(sensor_id), methods=value_method))
        print("SLI:", s_li)
        return s_li

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

    def after_update(self) -> None:
        self._current = self._read_temperature("temperature")



# todo Implement new many_from_host basing on extended state(each class initialising basing on: for each sensor in sensors: type:---
# to set device_class, native_unit_of_measurment, state class
