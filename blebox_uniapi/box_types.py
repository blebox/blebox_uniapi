from .cover import Gate, GateBox, GateBoxB, Shutter


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
    # airSensor
    "airSensor": {
        20180403: {
            "api_path": "/api/air/state",
            "air_qualities": [
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
        }
    },
    # gateBox
    "gateBox": {
        default_api_level: {
            # name of the subclass class of gatebox family
            "subclass": GateBox,
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
                ]
            ],
        },
        20200831: {
            # name of the subclass class of gatebox family
            "subclass": GateBoxB,
            "api_path": "/state",
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
                ]
            ],
        }
    },
    # gateController
    "gateController": {
        20180604: {
            # name of the subclass class of gate family
            "subclass": Gate,
            "api_path": "/api/gatecontroller/state",
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
                ]
            ],
        }
    },
    # saunaBox
    "saunaBox": {
        20180604: {
            # TODO: read extended state only once on startup
            "api_path": "/api/heat/extended/state",
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
    # thermoBox
    "thermoBox": {
        20180604: {
            # TODO: read extended state only once on startup
            "api_path": "/api/thermo/extended/state",
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
                        "desired": "thermo/desiredTemp",
                        "minimum": "thermo/minimumTemp",
                        "maximum": "thermo/maximumTemp",
                        "temperature": "sensors/[id=0]/value",
                        "state": "thermo/state",
                    },
                ]
            ],
        }
    },
    "shutterBox": {
        20180604: {
            # name of the subclass class of shutter family
            "subclass": Shutter,
            "api_path": "/api/shutter/state",
            "api": {
                "open": lambda x=None: ("GET", "/s/u", None),
                "close": lambda x=None: ("GET", "/s/d", None),
                "position": lambda x: ("GET", "/s/p/" + str(x), None),
                "stop": lambda x=None: ("GET", "/s/s", None),
            },
            "covers": [
                [
                    "position",
                    {
                        "desired": "shutter/desiredPos/position",
                        # "current": "shutter/currentPos/position",
                        "state": "shutter/state",
                    },
                    "shutter",
                ]
            ],
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
            "switches": [["0.relay", {"state": "[relay=0]/state"}, "relay"]],
        },
        20190808: {
            "api_path": "/api/relay/state",
            "api": {
                "on": lambda x=None: ("GET", "/s/1", None),
                "off": lambda x=None: ("GET", "/s/0", None),
            },
            "switches": [["0.relay", {"state": "relays/[relay=0]/state"}, "relay"]],
        }
    },
    # switchBoxD
    "switchBoxD": {
        20190808: {
            "api_path": "/api/relay/state",
            "api": {
                "on": lambda x: ("GET", f"/s/{int(x)}/1", None),
                "off": lambda x=None: ("GET", f"/s/{int(x)}/0", None),
            },
            "switches": [
                ["0.relay", {"state": "relays/[relay=0]/state"}, "relay", 0],
                ["1.relay", {"state": "relays/[relay=1]/state"}, "relay", 1],
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
        20180718: {
            "api_path": "/api/rgbw/state",
            "api": {
                "set": lambda x: (
                    "POST",
                    "/api/rgbw/set",
                    f'{{"rgbw":{{"desiredColor": "{str(x)}"}}}}',
                )
            },
            "lights": [
                [
                    "color",
                    {
                        "desired": "rgbw/desiredColor",
                        "last_color": "rgbw/lastOnColor",
                    },
                ]
            ],
        }
    },
    # wLightBoxS
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
            "lights": [["brightness", {"desired": "light/desiredColor"}]],
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
            "lights": [["brightness", {"desired": "rgbw/desiredColor"}]],
        }
    }
}
