

Integration for Blebox devices in Home Assistant.
=============

This documentation assumes you are familiar with Home Assistant and the Blebox devices.

How to Add a New Sensor (Based on MultiSensor Illuminance)
--------------------------------------------------------

1. **Update SENSOR_TYPES tuple in homeassistant.components.blebox.sensor module to allow creation of proper homeassistant entities for light readings depending on device capability reported by blebox_uniapi library.**:


   ```python
   from homeassistant.components.blebox.sensor import SensorEntityDescription, SensorDeviceClass
   from homeassistant.const import LIGHT_LUX

   SENSOR_TYPES = (
       # ... (existing entries)

       SensorEntityDescription(
           key="illuminance",
           device_class=SensorDeviceClass.ILLUMINANCE,
           native_unit_of_measurement=LIGHT_LUX,
       ),
   )```
2. **Update box_types module in blebox_uniapi to support new sensor types. (API level will be given, use newest version of the sensor if u want to copy paste)**
    ```python
    "multiSensor": {
        20220114: {
            "api_path": "/state",
            "extended_state_path": "/state/extended",
            "sensors": [
                [
                    "multiSensor",
                    {
                        "illuminance": lambda x:f"multiSensor/sensors/[id={x}]/value",
                        "temperature": lambda x: f"multiSensor/sensors/[id={x}]/value",
                        "wind": lambda x: f"multiSensor/sensors/[id={x}]/value",
                        "humidity": lambda x: f"multiSensor/sensors/[id={x}]/value",
                    },
                ]
            ],
            "binary_sensors": [
                [
                    "multiSensor",
                    {
                        "rain": lambda x: f"multiSensor/sensors/[id={x}]/value",
                        "flood": lambda x: f"multiSensor/sensors/[id={x}]/value",
                    },
                ]
            ],
        },
        ```
3. **Create new sensor class in blebox_uniapi.sensor module for light related readings updating type_class_mapper in blebox_uniapi.sensor.SensorFactory to return proper sensor class if device supports light related measurements**

    ```python
    class Illuminance(BaseSensor):
        def __init__(self, product: "Box", alias: str, methods: dict):
            super().__init__(product, alias, methods)
            self._unit = "lx"
            self._device_class = "illuminance"

        def _read_illuminance(self):
            product = self._product
            if product.last_data is not None:
                raw = self.raw_value("illuminance")
                if raw is not None:
                    alias = self._alias
                    return round(product.expect_int(alias, raw, 100000, 0)/100.0, 1)
            return None
    ```
    ```python
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
                "illuminance" : Illuminance
            }
    ```
