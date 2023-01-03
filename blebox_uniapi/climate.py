from .sensor import Temperature
from .error import JPathFailed
from typing import Optional, Any, Union
from .feature import Feature


class Climate(Temperature):
    _is_on: Optional[bool]
    _desired: Union[float, int, None]
    _is_heating: Optional[bool]
    _is_cooling: Optional[bool]
    _min_temp: Union[float, int, None]
    _max_temp: Union[float, int, None]
    _mode: Optional[int]
    _havc_action: Optional[int]

    def __init__(self, product, alias, methods, mode):
        super().__init__(product, alias, methods)
        self._mode = mode

    @property
    def mode(self) -> Optional[int]:
        return self._mode

    @property
    def is_on(self) -> Optional[bool]:
        return self._is_on

    @property
    def desired(self) -> Any:
        return self._desired

    @property
    def current(self) -> Any:
        return self._current

    @property
    def max_temp(self) -> Union[float, int, None]:
        return self._max_temp

    @property
    def min_temp(self) -> Union[float, int, None]:
        return self._min_temp

    @property
    def is_heating(self) -> Optional[bool]:
        return self._is_heating

    @property
    def is_cooling(self) -> Optional[bool]:
        return self._is_cooling

    @property
    def hvac_action(self) -> Optional[int]:
        return self._havc_action

    @classmethod
    def many_from_config(
        cls, product, box_type_config, extended_state
    ) -> list["Feature"]:
        # note: by default single config entry yields single feature instance but certain feature
        # domains (e.g. lights) may handle this differently depending on their `extended_state`
        alias, methods = box_type_config[0]
        if extended_state is not None:
            safetyIdPath = box_type_config[0][1].get("safetySensorId")
            if safetyIdPath:
                safety_sensor_id = product.follow(extended_state, safetyIdPath)
                temp_sensor_id = cls.get_temp_sensor_id(
                    safety_sensor_id, extended_state["sensors"]
                )
                methods = Feature.resolve_access_method_paths(methods, temp_sensor_id)

            args = [alias, methods]
            mode = extended_state.get("thermo", {}).get("mode", 1)
            return [cls(product, *args, mode)]
        return [cls(product, *args, 1) for args in box_type_config]

    async def async_on(self) -> None:
        await self.async_api_command("on")

    async def async_off(self) -> None:
        await self.async_api_command("off")

    async def async_set_temperature(self, value: Any) -> None:
        await self.async_api_command("set", int(round(value * 100.0)))

    def _read_is_on(self) -> Optional[bool]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value("state")
            if raw is not None:  # no reading
                alias = self._alias
                return product.expect_int(alias, raw, 3, 0) in (
                    1,
                    3,
                )  # 1: On, 3: Boost(thermoBox max temp of mode)
        return None

    def _read_operating_state(self) -> Optional[int]:
        """Return current operating state"""
        if self._product.last_data is not None:
            try:
                raw = self.raw_value("operatingState")
                if raw in range(0, 4) and isinstance(raw, int):
                    return raw
            except KeyError:
                return None

    def _read_is_heating(self) -> Optional[bool]:
        if not self._product.last_data:
            return None

        return self.is_on and (self.current < self.desired)

    def _read_is_cooling(self) -> Optional[bool]:
        if not self._product.last_data:
            return None

        return self.is_on and (self.current > self.desired)

    def _read_mode(self) -> Optional[int]:
        if self._product.last_data is not None:
            try:
                raw = self.raw_value("mode")
                if raw in range(0, 3) and isinstance(raw, int):
                    return raw
            except KeyError:
                return 1
        return None

    def after_update(self) -> None:
        self._is_on = self._read_is_on()
        self._desired = self._read_temperature("desired")
        self._current = self._read_temperature("temperature")
        self._is_heating = self._read_is_heating()
        self._is_cooling = self._read_is_cooling()
        self._havc_action = self._read_operating_state()
        if self._product.last_data is None:
            self._min_temp = None
            self._max_temp = None
            return

        try:
            self.raw_value("minimum")
        except JPathFailed:
            # TODO: coverage
            return

        self._min_temp = self._read_temperature("minimum")
        self._max_temp = self._read_temperature("maximum")

    @staticmethod
    def get_temp_sensor_id(safety_sensor_id: int, sensor_list) -> Optional[int]:
        """Return ID of first sensor which is not safety sensor."""
        li_sensor_id = list()
        for sensor in sensor_list:
            id = sensor.get("id")
            if id is not None and id != safety_sensor_id:
                li_sensor_id.append(sensor["id"])
        li_sensor_id.sort()

        if len(li_sensor_id) == False:
            return None

        return li_sensor_id[0]
