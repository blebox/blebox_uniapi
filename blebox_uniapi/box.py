# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import asyncio
import time
import traceback
from typing import Optional, Any, Dict, Union

from .air_quality import AirQuality
from .box_types import default_api_level, get_conf, get_conf_set
from .climate import Climate
from .cover import Cover
from .light import Light
from .sensor import Temperature
from .session import ApiHost
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
    HttpError,
)

import pdb

DEFAULT_PORT = 80


class Box:
    # TODO: pass IP? (For better error messages).
    def __init__(
        self,
        api_session: ApiHost,
        info: dict,
        config: dict,
        extended_state: Optional[Dict[Any, Any]],
    ) -> None:
        self._last_real_update: Optional[float] = None
        self._sem = asyncio.BoundedSemaphore()
        self._session = api_session
        self._name: str
        self._data_path: str

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

        # TODO: make wLightBox API support multiple products
        # in 2020 wLightBoxS API has been deprecated and it started using wLightBox API
        # current codebase needs a refactor to support multiple product sharing one API
        # as a temporary workaround we are using 'alias' type wLightBoxS2
        if type == "wLightBox" and product == "wLightBoxS":
            type = "wLightBoxS"

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

        level = int(info.get("apiLevel", default_api_level))

        self._data_path = config["api_path"]
        self._type = type
        self._unique_id = unique_id
        self._name = name
        self._firmware_version = firmware_version
        self._hardware_version = hardware_version
        self._api_version = level

        self._model = config.get("model", type)

        self._api = config.get("api", {})
        # todo get extended_state as param for init

        self._features = self.create_features(config, info, extended_state)

        self._config = config

        self._update_last_data(None)
        # pdb.set_trace()

    def create_features(self, config: dict, info: dict, extended_state: Optional[dict]) -> dict:
        features = {}
        print(f"estate: {extended_state}")
        for field, klass in {
            "air_qualities": AirQuality,
            "covers": Cover,
            "sensors": Temperature,  # TODO: too narrow
            "lights": Light,
            "climates": Climate,
            "switches": Switch,
        }.items():
            print(f"Create_features: {field}")
            try:
                features[field] = [
                    klass(self, *args) for args in config.get(field, [])  # todo taks 2
                ]
                print(features)
            # TODO: fix constructors instead
            except KeyError as ex:
                raise UnsupportedBoxResponse(info, f"Failed to initialize: {ex}")

        return features

    @classmethod
    async def async_from_host(cls, api_host: ApiHost) -> Box:
        try:
            path = "/api/device/state"
            data = await api_host.async_api_get(path)
        except HttpError:
            path = "/info"
            data = await api_host.async_api_get(path)

        info = data.get("device", data)  # type: ignore

        config = cls._match_device_config(info)

        try:
            extended_state = await api_host.async_api_get(config["extended_state_path"])
        except (HttpError, KeyError):
            extended_state = {}

        return cls(api_host, info, config, extended_state)

    @classmethod
    def _match_device_config(cls, info: dict) -> dict:
        try:
            type = info["type"]
        except KeyError as ex:
            raise UnsupportedBoxResponse(info, f"Device info has no type key") from ex
        try:
            product = info["product"]
        except KeyError:
            product = type
        if type == "wLightBox" and product == "wLightBoxS":
            type = "wLightBoxS"
        level = int(info.get("apiLevel", default_api_level))
        config_set = get_conf_set(type)
        if not config_set:
            raise UnsupportedBoxResponse(f"{type} is not a supported type")
        config = get_conf(level, config_set)
        if not config:
            raise UnsupportedBoxVersion(f"{type} has unsupported version ({level}).")

        return config

    @property
    def name(self) -> str:
        return self._name

    @property
    def last_data(self) -> Optional[Dict[Any, Any]]:
        return self._last_data

    @property
    def type(self) -> str:
        return self._type

    @property
    def unique_id(self) -> Any:
        return self._unique_id

    @property
    def firmware_version(self) -> Any:
        return self._firmware_version

    @property
    def hardware_version(self) -> Any:
        return self._hardware_version

    @property
    def api_version(self) -> int:
        return self._api_version

    @property
    def features(self) -> dict:
        return self._features

    @property
    def brand(self) -> str:
        return "BleBox"

    @property
    def model(self) -> Any:
        return self._model

    # TODO: report timestamp of last measurement (if possible)

    async def async_update_data(self) -> None:
        await self._async_api(True, "GET", self._data_path)

    def _update_last_data(self, new_data: Optional[dict]) -> None:
        self._last_data = new_data
        for feature_set in self._features.values():
            for feature in feature_set:
                feature.after_update()

    async def async_api_command(self, command: str, value: Any = None) -> None:
        method, *args = self._api[command](value)
        self._last_real_update = None  # force update
        return await self._async_api(False, method, *args)

    def follow(self, data: dict, path: str) -> Any:
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

    def expect_int(
        self, field: str, raw_value: int, maximum: int = -1, minimum: int = 0
    ) -> int:
        return self.check_int(raw_value, field, maximum, minimum)

    def expect_hex_str(
        self, field: str, raw_value: int, maximum: int = -1, minimum: int = 0
    ) -> int:
        return self.check_hex_str(raw_value, field, maximum, minimum)

    def expect_rgbw(self, field: str, raw_value: int) -> int:
        return self.check_rgbw(raw_value, field)

    def check_int_range(
        self, value: int, field: str, max_value: int, min_value: int
    ) -> int:
        if max_value >= min_value:
            if value > max_value:
                raise BadFieldExceedsMax(self.name, field, value, max_value)
            if value < min_value:
                raise BadFieldLessThanMin(self.name, field, value, min_value)

        return value

    def check_int(self, value: int, field: str, max_value: int, min_value: int) -> int:
        if value is None:
            raise BadFieldMissing(self.name, field)

        if not type(value) is int:
            raise BadFieldNotANumber(self.name, field, value)

        return self.check_int_range(value, field, max_value, min_value)

    def check_hex_str(
        self, value: int, field: str, max_value: int, min_value: int
    ) -> int:
        if value is None:
            raise BadFieldMissing(self.name, field)

        if not isinstance(value, str):
            raise BadFieldNotAString(self.name, field, value)

        return self.check_int_range(int(value, 16), field, max_value, min_value)

    def check_rgbw(self, value: int, field: str) -> int:
        if value is None:
            raise BadFieldMissing(self.name, field)

        if not isinstance(value, str):
            raise BadFieldNotAString(self.name, field, value)

        # value can have different length depending on LED color mode
        # mono mode will be 1 byte, and RGBWW will be 5 bytes
        if len(value) > 10 or len(value) % 2 != 0:
            raise BadFieldNotRGBW(self.name, field, value)
        return value

    def _has_recent_data(self) -> bool:
        last = self._last_real_update
        return (time.time() - 2) <= last if last is not None else False

    async def _async_api(
        self,
        is_update: bool,
        method: Any,
        path: str,
        post_data: dict = None,
    ) -> None:
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
