# -*- coding: utf-8 -*-

import semver
import re

# TODO: rename each to *State?
from .feature import (
    Temperature,
    Cover,
    AirQuality,
    Light,
    Climate,
    Switch,
)

DEFAULT_PORT = 80


class BoxError(RuntimeError):
    pass


# TODO: test exceptions


class UnsupportedBoxVersion(BoxError):
    pass


class UnsupportedAppVersion(BoxError):
    pass


class OutdatedBoxVersion(BoxError):
    pass


class JPathFailed(BoxError):
    pass


class BadFieldExceedsMax(BoxError):
    pass


class BadFieldLessThanMin(BoxError):
    pass


class BadFieldMissing(BoxError):
    pass


class BadFieldNotANumber(BoxError):
    pass


class BadFieldNotAString(BoxError):
    pass


class BadFieldNotRGBW(BoxError):
    pass


class UnsupportedBoxResponse(BoxError):
    pass


class Box:
    def __init__(self, api_session, info, state_root=None):
        self._session = api_session
        self._name = "(unnamed)"
        self._last_data = state_root
        self._data_path = None

        try:
            self._name = info["deviceName"]
            self._unique_id = info["id"]
            self._type = info["type"]
            self._firmware_version = info["fv"]
            self._hardware_version = info["hv"]

            # Here due to circular dependency
            from .products import Products

            config = Products.CONFIG["types"][self._type]
            self._version, self._outdated = self.extract_version(
                self._type, info, config
            )
            self._data_path = config["api_path"]
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
                self._features[field] = [
                    klass(self, *args) for args in config.get(field, [])
                ]

            self._config = config
        except KeyError as e:
            raise UnsupportedBoxResponse(info, e)

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
    def ipv4_address(self):
        return self._ipv4_address

    @property
    def features(self):
        return self._features

    @property
    def outdated(self):
        # TODO: fixme
        return self._outdated

    # TODO: report timestamp of last measurement (if possible)

    async def async_update_data(self):
        self._last_data = await self.async_api_call(self._data_path)

    def extract_version(self, type, device_info, config):
        min_supported, max_supported = config["api_level_range"]

        try:
            level = int(device_info["apiLevel"])
        except KeyError:
            if type != "gateBox":
                raise UnsupportedBoxResponse(device_info)

            # TODO: assume all are supported
            level = min_supported

        minor = level - min_supported
        if minor < 0:
            raise UnsupportedBoxVersion(device_info)

        current = semver.VersionInfo(1, minor, 0)
        if semver.VersionInfo.parse("1.0.0") > current:
            raise OutdatedBoxVersion(device_info)

        # TODO: for now, BleBox assumes backward-compatibility
        max_minor = max_supported - min_supported
        max_version = semver.VersionInfo(1, max_minor, 0)
        # if current > max_version:
        #     raise UnsupportedAppVersion(device_info)

        outdated = current < max_version
        return (current, outdated)

    async def async_api_call(self, path):
        return await self._session.async_api_get(path)

    async def async_api_command(self, command, value=None):
        method, path, post_data = self._api[command](value)
        if method not in ("GET", "POST"):
            raise NotImplementedError(method)

        if method == "GET":
            self._last_data = await self.async_api_call(path)
        else:
            self._last_data = await self._session.async_api_post(path, post_data)

    def follow(self, data, path):
        if data is None:
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
                    raise JPathFailed(f"with: {name}={value}")

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
                    raise JPathFailed(f"with: {name}={value}")
                continue

            with_index = re.compile("^\\[(\\d+)\\]$")
            match = with_index.match(chunk)
            if match:
                index = int(match.group(1))
                if not isinstance(current_tree, list) or index >= len(current_tree):
                    raise JPathFailed(f"with value at : {index}")

                current_tree = current_tree[index]
                continue

            if isinstance(current_tree, dict):
                names = current_tree.keys()
                if chunk not in names:
                    raise JPathFailed(f"item: {chunk} not among: {names}")

                current_tree = current_tree[chunk]
            else:
                raise JPathFailed(
                    f"unexpected type item: '{chunk}' not in: {current_tree}"
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
