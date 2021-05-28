# -*- coding: utf-8 -*-

import semver
import re
import asyncio
import time

from .sensor import Temperature
from .cover import Cover
from .air_quality import AirQuality
from .light import Light
from .climate import Climate
from .switch import Switch

from .error import (
    UnsupportedBoxResponse,
    UnsupportedBoxVersion,
    JPathFailed,
    BadFieldExceedsMax,
    BadFieldLessThanMin,
    BadFieldMissing,
    BadFieldNotANumber,
    BadFieldNotAString,
    BadFieldNotRGBW,
)

DEFAULT_PORT = 80


class Box:
    # TODO: pass IP? (For better error messages).
    def __init__(self, api_session, info):
        self._last_real_update = None
        self._sem = asyncio.BoundedSemaphore()
        self._session = api_session
        self._name = "(unnamed)"
        self._data_path = None

        address = f"{api_session.host}:{api_session.port}"

        location = f"Device at {address}"

        # NOTE: get ID first for better error messages
        try:
            unique_id = info["id"]
        except KeyError as ex:
            raise UnsupportedBoxResponse(info, f"{location} has no id") from ex
        location = f"Device:{unique_id} at {address}"

        try:
            type = info["type"]
        except KeyError as ex:
            raise UnsupportedBoxResponse(info, f"{location} has no type") from ex

        try:
            product = info["product"]
        except KeyError:
            product = type

        location = f"{product}:{unique_id} at {address}"

        try:
            name = info["deviceName"]
        except KeyError as ex:
            raise UnsupportedBoxResponse(info, f"{location} has no name") from ex
        location = f"'{name}' ({product}:{unique_id} at {address})"

        try:
            firmware_version = info["fv"]
        except KeyError as ex:
            raise UnsupportedBoxResponse(
                info, f"{location} has no firmware version"
            ) from ex
        location = f"'{name}' ({product}:{unique_id}/{firmware_version} at {address})"

        try:
            hardware_version = info["hv"]
        except KeyError as ex:
            raise UnsupportedBoxResponse(
                info, f"{location} has no hardware version"
            ) from ex

        try:
            level = int(info["apiLevel"])
        except KeyError:
            if type != "gateBox":
                raise UnsupportedBoxResponse(info, f"{location} has no apiLevel")

            level = None

        if type == "switchBox":
            if level < 20190808:
                type = "switchBox0"

        # Here due to circular dependency
        from .products import Products

        try:
            config = Products.CONFIG["types"][type]
        except KeyError as ex:
            raise UnsupportedBoxResponse(
                info, f"{location} is not a supported type"
            ) from ex

        # TODO: make wLightBox API support multiple products
        # in 2020 wLightBoxS API has been deprecated and it started using wLightBox API
        # current codebase needs a refactor to support multiple product sharing one API
        # as a temporary workaround we are using 'alias' type wLightBoxS2
        if type == "wLightBox" and product == "wLightBoxS":
            config = Products.CONFIG["types"]["wLightBoxS2"]
            type = "wLightBoxS"

        # Currently code doesn't support different apis for the same types or products
        # and should be heavily refactored to support that functionality.
        if type == "gateBox" and level:
            _min, _max = Products.CONFIG["types"]["gateBoxB"]["api_level_range"]
            if _min <= level <= _max:
                config = Products.CONFIG["types"]["gateBoxB"]
                type = "gateBoxB"

        # Ok to crash here, since it's a bug
        self._data_path = config["api_path"]
        min_supported, max_supported = config["api_level_range"]

        # TODO: assume all are supported
        if level is None:
            level = min_supported

        if level < min_supported:
            raise UnsupportedBoxVersion(
                info,
                f"{location} has outdated firmware (last supported: {min_supported} vs {level}) .",
            )

        version, outdated = self.extract_version(
            type, info, min_supported, max_supported, level
        )

        self._type = type
        self._product = product
        self._unique_id = unique_id
        self._name = name
        self._firmware_version = firmware_version
        self._hardware_version = hardware_version
        self._api_version = level
        self._version = version
        self._outdated = outdated
        self._model = config.get("model", type)

        self._api = config.get("api", {})

        self._features = {}
        for item in {
            "air_qualities": AirQuality,
            "covers": Cover,
            "sensors": Temperature,  # TODO: too narrow
            "lights": Light,
            "climates": Climate,
            "switches": Switch,
        }.items():
            field, klass = item
            try:
                self._features[field] = [
                    klass(self, *args) for args in config.get(field, [])
                ]
            # TODO: fix constructors instead
            except KeyError as ex:
                raise UnsupportedBoxResponse(
                    info, f"{location} failed to initialize: {ex}"
                )  # from ex

        self._config = config

        self._update_last_data(None)

    @property
    def name(self):
        return self._name

    @property
    def last_data(self):
        return self._last_data

    @property
    def type(self):
        return self._type

    @property
    def product(self):
        return self._product

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def firmware_version(self):
        return self._firmware_version

    @property
    def hardware_version(self):
        return self._hardware_version

    @property
    def api_version(self):
        return self._api_version

    @property
    def version(self):
        return self._version

    @property
    def features(self):
        return self._features

    @property
    def outdated(self):
        # TODO: fixme
        return self._outdated

    @property
    def brand(self):
        return "BleBox"

    @property
    def model(self):
        return self._model

    # TODO: report timestamp of last measurement (if possible)

    async def async_update_data(self):
        await self._async_api(True, "GET", self._data_path)

    def _update_last_data(self, new_data):
        self._last_data = new_data
        for feature_set in self._features.values():
            for feature in feature_set:
                feature.after_update()

    def extract_version(self, type, device_info, min_supported, max_supported, level):
        minor = level - min_supported

        current = semver.VersionInfo(1, minor, 0)

        # TODO: uncomment when compatiblity is broken
        # min_compatibility = config['min_semver'] # e.g. "1.0.0"
        # if semver.VersionInfo.parse(min_compatibility) > current:
        #     # TODO: coverage
        #     raise OutdatedBoxVersion(device_info)

        # TODO: for now, BleBox assumes backward-compatibility
        max_minor = max_supported - min_supported
        latest_version = semver.VersionInfo(1, max_minor, 0)

        # TODO: uncomment when backward compatiblity is broken
        # if current > latest_version:
        #     raise UnsupportedAppVersion(device_info)

        outdated = current < latest_version
        return (current, outdated)

    async def async_api_command(self, command, value=None):
        method, *args = self._api[command](value)
        self._last_real_update = None  # force update
        return await self._async_api(False, method, *args)

    def follow(self, data, path):
        if data is None:
            raise RuntimeError(f"bad argument: data {data}")  # pragma: no cover

        results = path.split("/")
        current_tree = data

        for chunk in results:
            with_string_value = re.compile("^\\[(.*)='(.*)'\\]$")

            match = with_string_value.match(chunk)
            if match:
                name = match.group(1)
                value = match.group(2)

                found = False

                for item in current_tree:
                    if item[name] == value:
                        current_tree = item
                        found = True
                        break

                if not found:
                    raise JPathFailed(f"with: {name}={value}", path, data)

                continue  # pragma: no cover

            with_int_value = re.compile("^\\[(.*)=(\\d+)\\]$")
            match = with_int_value.match(chunk)
            if match:
                name = match.group(1)
                value = int(match.group(2))

                found = False

                if not isinstance(current_tree, list):
                    raise JPathFailed(
                        f"list expected but got {current_tree}", path, data
                    )

                for item in current_tree:
                    if item[name] == value:
                        current_tree = item
                        found = True
                        break

                if not found:
                    raise JPathFailed(f"with: {name}={value}", path, data)
                continue  # pragma: no cover

            with_index = re.compile("^\\[(\\d+)\\]$")
            match = with_index.match(chunk)
            if match:
                index = int(match.group(1))
                if not isinstance(current_tree, list) or index >= len(current_tree):
                    raise JPathFailed(f"with value at index {index}", path, data)

                current_tree = current_tree[index]
                continue

            if isinstance(current_tree, dict):
                names = current_tree.keys()
                if chunk not in names:
                    raise JPathFailed(
                        f"item '{chunk}' not among {list(names)}", path, data
                    )

                current_tree = current_tree[chunk]
            else:
                raise JPathFailed(
                    f"unexpected item type: '{chunk}' not in: {current_tree}",
                    path,
                    data,
                )

        return current_tree

    def expect_int(self, field, raw_value, maximum=-1, minimum=0):
        return self.check_int(raw_value, field, maximum, minimum)

    def expect_hex_str(self, field, raw_value, maximum=-1, minimum=0):
        return self.check_hex_str(raw_value, field, maximum, minimum)

    def expect_rgbw(self, field, raw_value):
        return self.check_rgbw(raw_value, field)

    def check_int_range(self, value, field, max, min):
        if max >= min:
            if value > max:
                raise BadFieldExceedsMax(self.name, field, value, max)
            if value < min:
                raise BadFieldLessThanMin(self.name, field, value, min)

        return value

    def check_int(self, value, field, maximum, minimum):
        if value is None:
            raise BadFieldMissing(self.name, field)

        if not type(value) is int:
            raise BadFieldNotANumber(self.name, field, value)

        return self.check_int_range(value, field, maximum, minimum)

    def check_hex_str(self, value, field, maximum, minimum):
        if value is None:
            raise BadFieldMissing(self.name, field)

        if not isinstance(value, str):
            raise BadFieldNotAString(self.name, field, value)

        return self.check_int_range(int(value, 16), field, maximum, minimum)

    def check_rgbw(self, value, field):
        if value is None:
            raise BadFieldMissing(self.name, field)

        if not isinstance(value, str):
            raise BadFieldNotAString(self.name, field, value)

        # value can have different length depending on LED color mode
        # mono mode will be 1 byte, and RGBWW will be 5 bytes
        if len(value) > 10 or len(value) % 2 != 0:
            raise BadFieldNotRGBW(self.name, field, value)
        return value

    def _has_recent_data(self):
        last = self._last_real_update
        return time.time() - 2 <= last if last is not None else False

    async def _async_api(self, is_update, method, path, post_data=None):
        if method not in ("GET", "POST"):
            raise NotImplementedError(method)  # pragma: no cover

        if is_update:
            if self._has_recent_data():
                return

        async with self._sem:
            if is_update:
                if self._has_recent_data():
                    return

            if method == "GET":
                response = await self._session.async_api_get(path)
            else:
                response = await self._session.async_api_post(path, post_data)
            self._update_last_data(response)
            self._last_real_update = time.time()
