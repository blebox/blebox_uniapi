from typing import Union, TYPE_CHECKING

from .feature import Feature

if TYPE_CHECKING:
    from .box import Box


class BinarySensor(Feature):
    """Class representing sensor with bool state."""

    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)

    @classmethod
    def many_from_config(
        cls, product, box_type_config, extended_state
    ) -> list["Feature"]:
        type_class_map = {
            "rain": Rain,
            "flood": Flood,
        }

        output_list = list()
        sensors_list = extended_state.get("multiSensor").get("sensors", {})
        alias, methods = box_type_config[0]

        for sensor in sensors_list:
            sensor_type = sensor.get("type")
            sensor_id = sensor.get("id")

            if sensor_type in type_class_map:
                klass = type_class_map[sensor_type]

                if methods.get(sensor_type) is not None:
                    value_method = {sensor_type: methods[sensor_type](sensor_id)}
                    output_list.append(
                        klass(
                            product=product,
                            alias=sensor_type + "_" + str(sensor_id),
                            methods=value_method,
                        )
                    )

        return output_list


class Rain(BinarySensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        self._device_class = "moisture"
        super().__init__(product, alias, methods)

    @property
    def state(self) -> bool:
        return self._current > 0

    @property
    def device_class(self) -> str:
        return self._device_class

    def _read_rain(self, field: str) -> Union[float, int, None]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(field)
            if raw is not None:  # no reading
                return self.raw_value("rain")
        return 0

    def after_update(self) -> None:
        self._current = self._read_rain("rain")


class Flood(BinarySensor):
    def __init__(self, product: "Box", alias: str, methods: dict):
        self._device_class = "moisture"
        super().__init__(product, alias, methods)

    @property
    def state(self) -> bool:
        return self._current > 0

    @property
    def device_class(self) -> str:
        return self._device_class

    def _read_flood(self, field: str) -> Union[float, int, None]:
        product = self._product

        if product.last_data is not None:
            raw = self.raw_value(field)
            if raw is not None:  # no reading
                return self.raw_value("flood")
        return 0

    def after_update(self) -> None:
        self._current = self._read_flood("flood")
