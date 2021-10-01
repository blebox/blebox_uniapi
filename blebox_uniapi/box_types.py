from .air_quality import AirQuality
from .climate import Climate
from .cover import Cover, Gate, GateBox, GateBoxB, Shutter
from .light import Light
from .sensor import Sensor, Temperature
from .switch import Switch



# default api level for all products that don't have one
default_api_level = 20151206


def get_conf_set(product_type):
    """Get all configurations for provided product type."""
    conf_set = BOX_TYPE_CONF.get(product_type, {})
    return conf_set


def get_conf(api_level, conf_set):
    """Get configuration from conf_set for provided api_level."""
    for min_api_level in sorted(conf_set, reverse=True):
        if api_level >= min_api_level:
            return conf_set[min_api_level]

    return {}


def get_latest_conf(product_type):
    """Get latest configuration for provided product type."""
    conf_set = get_conf_set(product_type)
    if conf_set:
        latest_min_api_level = sorted(conf_set, reverse=True)[0]
        return conf_set[latest_min_api_level]

    return conf_set


def get_latest_api_level(product_type):
    """Get latest supported api_level for provided product type."""
    conf_set = get_conf_set(product_type)
    if conf_set:
        return sorted(conf_set, reverse=True)[0]

    return 0


# Configuration for all box types
BOX_TYPE_CONF = {
    "airSensor": {
        20180403: {
            "api_path": "/api/air/state",
            "class": AirQuality,
            "entity_type": "air_qualities",
            "methods": [
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
            ]
        }
    },
    "gateBox": {
        default_api_level: {
            "api_path": "/api/gate/state",
            "api": {
                "primary": lambda x=None: ("GET", "/s/p", None),
                "secondary": lambda x=None: ("GET", "/s/s", None),
            },
            "class": Cover,
            "subclass": GateBox,
            "entity_type": "covers",
            "methods": [
                [
                    "position",
                    {
                        "position": "currentPos",
                        "desired": "desiredPos",
                        "extraButtonType": "extraButtonType",
                    },
                    "gatebox",
                ]
            ]
        },
        20200831: {
            "api_path": "/state",
            "api": {
                "primary": lambda x=None: ("GET", "/s/p", None),
                "secondary": lambda x=None: ("GET", "/s/s", None),
            },
            "class": Cover,
            "subclass": GateBoxB,
            "entity_type": "covers",
            "methods": [
                [
                    "position",
                    {
                        "position": "gate/currentPos",
                    },
                    "gatebox",
                ]
            ]
        }
    },
    "gateController": {
        20180604: {
            "api_path": "/api/gatecontroller/state",
            "api": {
                "open": lambda x=None: ("GET", "/s/o", None),
                "close": lambda x=None: ("GET", "/s/c", None),
                "position": lambda x: ("GET", "/s/p/" + str(x), None),
                "stop": lambda x=None: ("GET", "/s/s", None),
            },
            "class": Cover,
            "subclass": Gate,
            "entity_type": "covers",
            "methods": [
                [
                    "position",
                    {
                        "desired": "gateController/desiredPos/positions/[0]",
                        "state": "gateController/state",
                    },
                    "gate",
                ]
            ]
        }
    },
    "saunaBox": {
        20180604: {
            # TODO: read extended state only once on startup
            "api_path": "/api/heat/extended/state",
            "api": {
                "on": lambda x=None: ("GET", "/s/1", None),
                "off": lambda x=None: ("GET", "/s/0", None),
                "set": lambda x=None: ("GET", "/s/t/" + str(x), None),
            },
            "class": Climate,
            "entity_type": "climates",
            "methods": [
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
            ]
        }
    },
    "shutterBox": {
        20180604: {
            "api_path": "/api/shutter/state",
            "api": {
                "open": lambda x=None: ("GET", "/s/u", None),
                "close": lambda x=None: ("GET", "/s/d", None),
                "position": lambda x: ("GET", "/s/p/" + str(x), None),
                "stop": lambda x=None: ("GET", "/s/s", None),
            },
            "class": Cover,
            "subclass": Shutter,
            "entity_type": "covers",
            "methods": [
                [
                    "position",
                    {
                        "desired": "shutter/desiredPos/position",
                        "state": "shutter/state",
                    },
                    "shutter",
                ]
            ]
        }
    },
    "switchBox": {
        20180604: {
            "model": "switchBox",
            "api_path": "/api/relay/state",
            "api": {
                "on": lambda x=None: ("GET", "/s/1", None),
                "off": lambda x=None: ("GET", "/s/0", None),
            },
            "class": Switch,
            "entity_type": "switches",
            "methods": [["0.relay", {"state": "[relay=0]/state"}, "relay"]]
        },
        20190808: {
            "api_path": "/api/relay/state",
            "api": {
                "on": lambda x=None: ("GET", "/s/1", None),
                "off": lambda x=None: ("GET", "/s/0", None),
            },
            "class": Switch,
            "entity_type": "switches",
            "methods": [["0.relay", {"state": "relays/[relay=0]/state"}, "relay"]]
        }
    },
    "switchBoxD": {
        20190808: {
            "api_path": "/api/relay/state",
            "api": {
                "on": lambda x: ("GET", f"/s/{int(x)}/1", None),
                "off": lambda x=None: ("GET", f"/s/{int(x)}/0", None),
            },
            "class": Switch,
            "entity_type": "switches",
            "methods": [
                ["0.relay", {"state": "relays/[relay=0]/state"}, "relay", 0],
                ["1.relay", {"state": "relays/[relay=1]/state"}, "relay", 1],
            ]
        }
    },
    "tempSensor": {
        20180604: {
            "api_path": "/api/tempsensor/state",
            "class": Temperature,
            "entity_type": "sensors",
            "methods": [
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
    "dimmerBox": {
        20170829: {
            "api_path": "/api/dimmer/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/dimmer/set",
                    '{"dimmer":{"desiredBrightness": ' + str(x) + "}}",
                ),
            },
            "class": Light,
            "entity_type": "lights",
            "methods": [["brightness", {"desired": "dimmer/desiredBrightness"}]],
        }
    },
    "wLightBox": {
        20180718: {
            "api_path": "/api/rgbw/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/rgbw/set",
                    f'{{"rgbw":{{"desiredColor": "{str(x)}"}}}}',
                )
            },
            "class": Light,
            "entity_type": "lights",
            "methods": [
                ["color", {"desired": "rgbw/desiredColor", "last_color": "rgbw/lastOnColor"}]
            ],
        }
    },
    "wLightBoxS": {
        20180718: {
            "api_path": "/api/light/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/light/set",
                    f'{{"light": {{"desiredColor": "{x}"}}}}',
                )
            },
            "class": Light,
            "entity_type": "lights",
            "methods": [["brightness", {"desired": "light/desiredColor"}]],
        },
        20200229: {
            "api_path": "/api/rgbw/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/rgbw/set",
                    f'{{"rgbw": {{"desiredColor": "{x}"}}}}',
                )
            },
            "class": Light,
            "entity_type": "lights",
            "methods": [["brightness", {"desired": "rgbw/desiredColor"}]],
        }
    },
    "multiSensor": {
        20210413: {
            "api_path": "/state",
            "class": Sensor,
            "entity_type": "sensors",
            "methods": [
                # leave empty if methods should be provided dynamically
            ],
        }
    }
}
