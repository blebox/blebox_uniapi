from .box import Box

from .error import UnsupportedBoxResponse


class Products:
    # TODO: convert to json?
    CONFIG = {
        "types": {
            "airSensor": {
                "api_path": "/api/air/state",
                "api_level_range": [20180403, 20191112],
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
            },
            "dimmerBox": {
                "api_path": "/api/dimmer/state",
                "api_level_range": [20170829, 20170829],
                "api": {
                    "set": lambda x: (
                        "POST",
                        "/api/dimmer/set",
                        '{"dimmer":{"desiredBrightness": ' + str(x) + "}}",
                    ),
                },
                "lights": [["brightness", {"desired": "dimmer/desiredBrightness"}]],
            },
            "gateBox": {
                "api_path": "/api/gate/state",
                "api_level_range": [20161213, 20161213],
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
            "gateController": {
                "api_path": "/api/gatecontroller/state",
                "api_level_range": [20180604, 20190911],
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
                            "desired": "gateController/desiredPos/[0]",
                            # "current": "gateController/currentPos/[0]",
                            "state": "gateController/state",
                        },
                        "gate",
                    ]
                ],
            },
            "saunaBox": {
                "api_path": "/api/heat/state",
                # TODO: use an api map (map to semver)? Or constraints?
                "api_level_range": [20180604, 20180604],
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
                            "temperature": "heat/sensors/[id=0]/value",
                            "state": "heat/state",
                        },
                    ]
                ],
            },
            "shutterBox": {
                "api_path": "/api/shutter/state",
                "api_level_range": [20180604, 20190911],
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
            },
            "switchBox": {
                "api_path": "/api/relay/state",
                "api_level_range": [20180604, 20190808],
                "api": {
                    "on": lambda x=None: ("GET", "/s/1", None),
                    "off": lambda x=None: ("GET", "/s/0", None),
                },
                "switches": [["0.relay", {"state": "relays/[relay=0]/state"}, "relay"]],
            },
            "switchBoxD": {
                "api_path": "/api/relay/state",
                "api_level_range": [20190808, 20190808],
                "api": {
                    "on": lambda x: ("GET", f"/s/{int(x)}/1", None),
                    "off": lambda x=None: ("GET", f"/s/{int(x)}/0", None),
                },
                "switches": [
                    ["0.relay", {"state": "relays/[relay=0]/state"}, "relay", 0],
                    ["1.relay", {"state": "relays/[relay=1]/state"}, "relay", 1],
                ],
            },
            "tempSensor": {
                "api_path": "/api/tempsensor/state",
                "api_level_range": [20180604, 20180604],
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
            },
            "wLightBox": {
                "api_path": "/api/rgbw/state",
                "api_level_range": [20180718, 20190808],
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
            },
            "wLightBoxS": {
                "api_path": "/api/light/state",
                "api_level_range": [20180718, 20180718],
                "api": {
                    "set": lambda x: (
                        "POST",
                        "/api/rgbw/set",
                        f'{{"light": {{"desiredColor": "{x}"}}}}',
                    )
                },
                "lights": [["color", {"desired": "light/desiredColor"}]],
            },
        }
    }

    @staticmethod
    async def async_from_host(api_host):
        path = "/api/device/state"
        data = await api_host.async_api_get(path)
        product = Products.from_data(data, api_host)
        return product

    @staticmethod
    def from_data(root, api_host):
        try:
            info = root["device"]
            data = {
                "switchBox": [info],
                "dimmerBox": [info, root],
                "wLightBoxS": [info],
                "wLightBox": [info],
                "gateController": [info],
                "saunaBox": [info],
                "switchBoxD": [info],
                "shutterBox": [info],
                "tempSensor": [info],
                # in case it's ever fixed
                "airSensor": [info],
                "gateBox": [info],
            }
        except KeyError:
            info = root
            data = {
                "airSensor": [root],
                "gateBox": [root],
            }

        try:
            product_type = info["type"]
        except KeyError:
            # TODO: coverage
            raise UnsupportedBoxResponse("(no type in info)")

        try:
            args = data[product_type]
        except KeyError:
            raise UnsupportedBoxResponse(product_type)

        return Box(api_host, *args)
