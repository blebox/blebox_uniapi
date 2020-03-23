# -*- coding: utf-8 -*-

import semver
import re

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
    def __init__(self, api_session, info, state_root=None):
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
        location = f"{type}:{unique_id} at {address}"

        # Here due to circular dependency
        from .products import Products

        try:
            config = Products.CONFIG["types"][type]
        except KeyError as ex:
            raise UnsupportedBoxResponse(
                info, f"{location} is not a supported type"
            ) from ex

        # Ok to crash here, since it's a bug
        self._data_path = config["api_path"]
        min_supported, max_supported = config["api_level_range"]

        try:
            name = info["deviceName"]
        except KeyError as ex:
            raise UnsupportedBoxResponse(info, f"{location} has no name") from ex
        location = f"'{name}' ({type}:{unique_id} at {address})"

        try:
            firmware_version = info["fv"]
        except KeyError as ex:
            raise UnsupportedBoxResponse(
                info, f"{location} has no firmware version"
            ) from ex
        location = f"'{name}' ({type}:{unique_id}/{firmware_version} at {address})"

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

            # TODO: assume all are supported
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
        self._unique_id = unique_id
        self._name = name
        self._firmware_version = firmware_version
        self._hardware_version = hardware_version
        self._api_version = level
        self._version = version
        self._outdated = outdated

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

        self._update_last_data(state_root)

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

    # TODO: report timestamp of last measurement (if possible)

    async def async_update_data(self):
        self._update_last_data(await self.async_api_call(self._data_path))

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

    async def async_api_call(self, path):
        return await self._session.async_api_get(path)

    async def async_api_command(self, command, value=None):
        method, path, post_data = self._api[command](value)
        if method not in ("GET", "POST"):
            # TODO: coverage
            raise NotImplementedError(method)

        if method == "GET":
            self._update_last_data(await self.async_api_call(path))
        else:
            self._update_last_data(await self._session.async_api_post(path, post_data))

    def follow(self, data, path):
        if data is None:
            # TODO: coverage
            raise RuntimeError(f"bad argument: data {data}")

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

                continue

            with_int_value = re.compile("^\\[(.*)=(\\d+)\\]$")
            match = with_int_value.match(chunk)
            if match:
                name = match.group(1)
                value = int(match.group(2))

                found = False

                for item in current_tree:
                    if item[name] == value:
                        current_tree = item
                        found = True
                        break

                if not found:
                    raise JPathFailed(f"with: {name}={value}", path, data)
                continue

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

        if len(value) != 8:
            raise BadFieldNotRGBW(self.name, field, value)
        return value
