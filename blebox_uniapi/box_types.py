from .cover import Gate, GateBox, GateBoxB, Shutter
from typing import Union, Any

# default api level for all products that don't have one
default_api_level = 20151206


def get_conf_set(product_type: str) -> dict:
    """Get all configurations for provided product type."""
    conf_set = BOX_TYPE_CONF.get(product_type, {})
    return conf_set


def get_conf(api_level: Union[int, str], conf_set: dict) -> dict:
    """Get configuration from conf_set for provided api_level."""
    for min_api_level in sorted(conf_set, reverse=True):
        if api_level >= min_api_level:
            return conf_set[min_api_level]

    return {}


def get_latest_conf(product_type: str) -> dict:
    """Get latest configuration for provided product type."""
    conf_set = get_conf_set(product_type)
    if conf_set:
        latest_min_api_level = sorted(conf_set, reverse=True)[0]
        return conf_set[latest_min_api_level]

    return conf_set


def get_latest_api_level(product_type: str) -> Union[dict, int]:
    """Get latest supported api_level for provided product type."""
    conf_set = get_conf_set(product_type)
    if conf_set:
        return sorted(conf_set, reverse=True)[0]
    return 0


# Configuration for all box types

BOX_TYPE_CONF: dict[str, dict[int, dict[str, Any]]] = {
    # tvLiftBox; in comments api level config description
    "tvLiftBox": {  # apiType to match devices apiType
        20200518: {  # apiLevel to match integration level
            "api_path": "/api/device/state",  # path to devices state
            "extended_state_path": "/state/extended",  # path to devices extended state
            "api": {
                "set": lambda command: ("GET", f"/s/c/{command}")
            },  # dictionary with interaction methods
            "buttons": [
                "tvLift",
                {"lift": ""},
            ],  # key used to set platform, list elements used in cls init, e.g. [<alias>, {"path": "state_value"}]
        }
    },
    # airSensor
    "airSensor": {
        20180403: {
            "api_path": "/api/air/state",
            "sensors": [
                [
                    "0.air",
                    {
                        "pm1.value": "air/sensors/[type='pm1']/value",
                        "pm1.state": "air/sensors/[type='pm1']/state",
                        "pm2_5.value": "air/sensors/[type='pm2.5']/value",
                        "pm2_5.state": "air/sensors/[type='pm2.5']/state",
                        "pm10.value": "air/sensors/[type='pm10']/value",
                        "pm10.state": "air/sensors/[type='pm10']/state",
                    },
                ]
            ],
        }
    },
    # dimmerBox
    "dimmerBox": {
        default_api_level: {
            "api_path": "/api/dimmer/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/dimmer/set",
                    '{"dimmer":{"desiredBrightness": ' + str(x) + "}}",
                ),
            },
            "lights": [["brightness", {"desired": "dimmer/desiredBrightness"}]],
        },
        20170829: {
            "api_path": "/api/dimmer/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/dimmer/set",
                    '{"dimmer":{"desiredBrightness": ' + str(x) + "}}",
                ),
            },
            "lights": [["brightness", {"desired": "dimmer/desiredBrightness"}]],
        },
    },
    # gateBox
    "gateBox": {
        default_api_level: {
            "api_path": "/api/gate/state",
            "api": {
                "primary": lambda x=None: ("GET", "/s/p", None),
                "secondary": lambda x=None: ("GET", "/s/s", None),
            },
            "covers": [
                [
                    "position",
                    {
                        "position": "currentPos",
                        "desired": "desiredPos",
                        "extraButtonType": "extraButtonType",
                    },
                    "gatebox",
                    GateBox,
                ]
            ],
        },
        20200831: {
            "api_path": "/state",
            "extended_state_path": "/state/extended",
            "api": {
                "primary": lambda x=None: ("GET", "/s/p", None),
                "secondary": lambda x=None: ("GET", "/s/s", None),
            },
            "covers": [
                [
                    "position",
                    {
                        "position": "gate/currentPos",
                    },
                    "gatebox",
                    GateBoxB,
                ]
            ],
        },
    },
    # gateController
    "gateController": {
        20180604: {
            "api_path": "/api/gatecontroller/state",
            "extended_state_path": "/api/gatecontroller/extended/state",
            "api": {
                "open": lambda x=None: ("GET", "/s/o", None),
                "close": lambda x=None: ("GET", "/s/c", None),
                "position": lambda x: ("GET", "/s/p/" + str(x), None),
                "stop": lambda x=None: ("GET", "/s/s", None),
                # "walk": lambda x=None: ("GET", "/s/w", None),
                # "next": lambda x=None: ("GET", "/s/n", None),
            },
            "covers": [
                [
                    "position",
                    {
                        "desired": "gateController/desiredPos/positions/[0]",
                        # "current": "gateController/currentPos/positions/[0]",
                        "state": "gateController/state",
                    },
                    "gate",
                    Gate,
                ]
            ],
        }
    },
    # saunaBox
    "thermoBox": {
        20200229: {
            "api_path": "/state/extended",
            "extended_state_path": "/state/extended",
            "api": {
                "on": lambda x=None: ("GET", "/s/1", None),
                "off": lambda x=None: ("GET", "/s/0", None),
                "set": lambda x=None: ("GET", "/s/t/" + str(x), None),
            },
            "climates": [
                [
                    "thermostat",
                    {
                        "desired": "thermo/desiredTemp",
                        "minimum": "thermo/minimumTemp",
                        "maximum": "thermo/maximumTemp",
                        "temperature": lambda x: f"sensors/[id={x}]/value",
                        "state": "thermo/state",
                        "mode": "thermo/mode",
                        "safetySensorId": "thermo/safetyTempSensor/sensorId",
                        "operatingState": "thermo/operatingState",
                    },
                ]
            ],
        }
    },
    "saunaBox": {
        20180604: {
            # TODO: read extended state only once on startup
            "api_path": "/api/heat/extended/state",
            "extended_state_path": "/api/heat/extended/state",
            # TODO: use an api map (map to semver)? Or constraints?
            "api": {
                "on": lambda x=None: ("GET", "/s/1", None),
                "off": lambda x=None: ("GET", "/s/0", None),
                "set": lambda x=None: ("GET", "/s/t/" + str(x), None),
            },
            "climates": [
                [
                    "thermostat",
                    {
                        "desired": "heat/desiredTemp",
                        "minimum": "heat/minimumTemp",
                        "maximum": "heat/maximumTemp",
                        "temperature": "heat/sensors/[id=0]/value",
                        "state": "heat/state",
                    },
                ]
            ],
        }
    },
    "shutterBox": {
        20180604: {
            "api_path": "/api/shutter/state",
            "extended_state_path": "/api/shutter/extended/state",
            "api": {
                "open": lambda x=None: ("GET", "/s/u", None),
                "close": lambda x=None: ("GET", "/s/d", None),
                "position": lambda x: ("GET", "/s/p/" + str(x), None),
                "stop": lambda x=None: ("GET", "/s/s", None),
                "tilt": lambda x=None: ("GET", "/s/t/" + str(x), None),
            },
            "covers": [
                [
                    "position",
                    {
                        "desired": "shutter/desiredPos/position",
                        # "current": "shutter/currentPos/position",
                        "tilt": "shutter/desiredPos/tilt",
                        "state": "shutter/state",
                    },
                    "shutter",
                    Shutter,
                ]
            ],
        }
    },
    "switchBox": {
        20220114: {
            "api_path": "/state",
            "extended_state_path": "/state/extended",
            "api": {
                "on": lambda x=None: ("GET", f"/s/{x}/1", None),
                "off": lambda x=None: ("GET", f"/s/{x}/0", None),
            },
            "switches": [
                ["relay", {"state": lambda x: f"relays/[relay={x}]/state"}, "relay"]
            ],
        },
        20180604: {
            "model": "switchBox",
            "api_path": "/api/relay/state",
            "extended_state_path": "/api/relay/extended/state",
            "api": {
                "on": lambda x=None: ("GET", "/s/1", None),
                "off": lambda x=None: ("GET", "/s/0", None),
            },
            "switches": [["0.relay", {"state": "[relay=0]/state"}, "relay"]],
        },
        20190808: {
            "api_path": "/api/relay/extended/state",
            "extended_state_path": "/api/relay/extended/state",
            "api": {
                "on": lambda x=None: ("GET", "/s/1", None),
                "off": lambda x=None: ("GET", "/s/0", None),
            },
            "switches": [
                ["0.relay", {"state": lambda x: f"relays/[relay={x}]/state"}, "relay"]
            ],
            "sensors": [
                [
                    "switchBox.energy",
                    {
                        "energy": "powerMeasuring/powerConsumption/[0]/value",
                        "periodS": "powerMeasuring/powerConsumption/[0]/periodS",
                        "measurment_enabled": "powerMeasuring/enabled",
                    },
                ]
            ],
        },
    },
    # switchBoxD
    "switchBoxD": {
        20190808: {
            "extended_state_path": "/state/extended",  # tylko dla testów do usunięcia nie w tym api
            "api_path": "/state/extended",
            "api": {
                "on": lambda x: ("GET", f"/s/{int(x)}/1", None),
                "off": lambda x=None: ("GET", f"/s/{int(x)}/0", None),
            },
            "switches": [
                [
                    "0.relay",
                    {"state": lambda x: f"relays/[relay={x}]/state"},
                    "relay",
                    0,
                ],
                [
                    "1.relay",
                    {"state": lambda x: f"relays/[relay={x}]/state"},
                    "relay",
                    1,
                ],
            ],
            "sensors": [
                [
                    "switchBox.energy",
                    {
                        "energy": "powerMeasuring/powerConsumption/[0]/value",
                        "periodS": "powerMeasuring/powerConsumption/[0]/periodS",
                        "measurment_enabled": "powerMeasuring/enabled",
                    },
                ]
            ],
        }
    },
    # tempSensor
    "tempSensor": {
        20180604: {
            "api_path": "/api/tempsensor/state",
            "sensors": [
                [
                    "0.temperature",
                    {
                        "temperature": "tempSensor/sensors/[id=0]/value",
                        "trend": "tempSensor/sensors/[id=0]/trend",
                        "state": "tempSensor/sensors/[id=0]/state",
                        "elapsed": "tempSensor/sensors/[id=0]/elapsedTimeS",
                    },
                ]
            ],
        }
    },
    # wLightBox
    "wLightBox": {
        default_api_level: {
            "api_path": "/api/device/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/rgbw/set",
                    f'{{"rgbw":{{"desiredColor": "{str(x)}"}}}}',
                ),
            },
            "lights": [
                [
                    "color",
                    {
                        "desired": "rgbw/desiredColor",
                        "last_color": "rgbw/lastOnColor",
                        "currentEffect": "rgbw/effectID",
                        "colorMode": "rgbw/colorMode",
                    },
                ]
            ],
        },
        20190808: {
            "api_path": "/api/rgbw/state",
            "extended_state_path": "/api/rgbw/extended/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/rgbw/set",
                    f'{{"rgbw":{{"desiredColor": "{str(x)}"}}}}',
                ),
                "effect": lambda x: ("GET", f"/s/x/{x}", None),
            },
            "lights": [
                [
                    "color",
                    {
                        "desired": "rgbw/desiredColor",
                        "last_color": "rgbw/lastOnColor",
                        "currentEffect": "rgbw/effectID",
                        "colorMode": "rgbw/colorMode",
                    },
                ]
            ],
        },
        20200229: {
            "api_path": "/api/rgbw/state",
            "extended_state_path": "/api/rgbw/extended/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/rgbw/set",
                    f'{{"rgbw": {{"desiredColor": "{x}"}}}}',
                ),
                "effect": lambda x: ("GET", f"/s/x/{x}"),
            },
            "lights": [
                [
                    "color",
                    {
                        "desired": "rgbw/desiredColor",
                        "last_color": "rgbw/lastOnColor",
                        "currentEffect": "rgbw/effectID",
                        "colorMode": "rgbw/colorMode",
                    },
                ],
            ],
        },
    },
    # wLightBoxS
    "wLightBoxS": {
        default_api_level: {
            "api_path": "/api/device/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/light/set",
                    f'{{"light": {{"desiredColor": "{x}"}}}}',
                ),
            },
            "lights": [
                [
                    "brightness",
                    {
                        "desired": "light/desiredColor",
                    },
                ]
            ],
        },
        20180718: {
            "api_path": "/api/light/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/light/set",
                    f'{{"light": {{"desiredColor": "{x}"}}}}',
                ),
                "effect": lambda x: ("GET", f"/s/x/{x}"),
            },
            "lights": [
                [
                    "brightness",
                    {
                        "desired": "light/desiredColor",
                    },
                ]
            ],
        },
        20200229: {
            "api_path": "/api/rgbw/state",
            "extended_state_path": "/api/rgbw/extended/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/rgbw/set",
                    f'{{"rgbw": {{"desiredColor": "{x}"}}}}',
                ),
                "effect": lambda x: ("GET", f"/s/x/{x}"),
            },
            "lights": [
                [
                    "brightness",
                    {
                        "desired": "rgbw/desiredColor",
                        "colorMode": "rgbw/colorMode",
                        "currentEffect": "rgbw/effectID",
                        "last_color": "rgbw/lastOnColor",
                    },
                ]
            ],
        },
    },
    "multiSensor": {
        20210413: {
            "api_path": "/state",
            "extended_state_path": "/state/extended",
            "sensors": [
                [
                    "multiSensor",
                    {
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
                    },
                ]
            ],
        },
        20200831: {
            "api_path": "/state",
            "extended_state_path": "/state/extended",
            "sensors": [
                [
                    "multiSensor",
                    {
                        "temperature": lambda x: f"multiSensor/sensors/[id={x}]/value",
                        "wind": lambda x: f"multiSensor/sensors/[id={x}]/value",
                    },
                ]
            ],
            "binary_sensors": [
                [
                    "multiSensor",
                    {
                        "rain": lambda x: f"multiSensor/sensors/[id={x}]/value",
                    },
                ]
            ],
        },
    },
}
