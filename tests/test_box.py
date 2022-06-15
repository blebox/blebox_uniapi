import json

import pytest

from unittest import mock

from unittest.mock import patch

from blebox_uniapi.box import Box
from blebox_uniapi import error

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_session():
    return mock.MagicMock(host="172.1.2.3", port=80)


@pytest.fixture
def data():
    return {
        "id": "abcd1234ef",
        "type": "airSensor",
        "deviceName": "foobar",
        "fv": "1.23",
        "hv": "4.56",
        "apiLevel": "20180403",
    }


@pytest.fixture
def config(data):
    return Box._match_device_config(data)


async def test_json_paths(mock_session, data, config):
    box = Box(mock_session, data, config, None)

    assert "foo" == box.follow(json.loads("""["foo"]"""), "[0]")
    assert 4 == box.follow(
        json.loads("""[{"foo":"3", "value":4}]"""), "[foo='3']/value"
    )

    assert 4 == box.follow(json.loads("""[{"foo":3, "value":4}]"""), "[foo=3]/value")

    with pytest.raises(error.JPathFailed, match=r"with: foo=bc at .* within .*"):
        box.follow(json.loads("""[{"foo":"ab", "value":4}]"""), "[foo='bc']/value")

    with pytest.raises(
        error.JPathFailed, match=r"with value at index 1 at .* within .*"
    ):
        box.follow(json.loads("""[{"value":4}]"""), "[1]/value")

    with pytest.raises(
        error.JPathFailed, match=r"with value at index 1 at .* within .*"
    ):
        box.follow(json.loads("""{"value":4}"""), "[1]/value")

    with pytest.raises(error.JPathFailed, match=r"with: foo=7 at .* within .*"):
        box.follow(json.loads("""[{"foo":3, "value":4}]"""), "[foo=7]/value")

    with pytest.raises(
        error.JPathFailed, match=r"item 'foo' not among \['value'\] at .* within .*"
    ):
        box.follow(json.loads("""{"value":4}"""), "foo")

    with pytest.raises(
        error.JPathFailed,
        match=r"unexpected item type: 'foo' not in: \[4\] at .* within .*",
    ):
        box.follow(json.loads("""[4]"""), "foo")

    with pytest.raises(
        error.JPathFailed,
        match=r"list expected but got {'foo': \[4\]} at .* within .*",
    ):
        box.follow(json.loads("""{"foo": [4]}"""), "[bar=0]/value")


async def test_without_id(mock_session, data, config):
    with pytest.raises(
        error.UnsupportedBoxResponse, match="Device at 172.1.2.3:80 has no id"
    ):
        del data["id"]
        Box(mock_session, data, config, None)


async def test_without_type(mock_session, data, config):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match="Device:abcd1234ef at 172.1.2.3:80 has no type",
    ):
        del data["type"]
        Box(mock_session, data, config, None)


async def test_with_unknown_type(mock_session, data):
    with pytest.raises(error.UnsupportedBoxResponse, match=r"type"):
        data["type"] = "unknownBox"
        Box._match_device_config(data)


async def test_without_name(mock_session, data, config):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match="airSensor:abcd1234ef at 172.1.2.3:80 has no name",
    ):
        del data["deviceName"]
        Box(mock_session, data, config, None)


async def test_without_firmware_version(mock_session, data, config):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match=r"'foobar' \(airSensor:abcd1234ef at 172.1.2.3:80\) has no firmware version",
    ):
        del data["fv"]
        Box(mock_session, data, config, None)


async def test_without_hardware_version(mock_session, data, config):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match=r"'foobar' \(airSensor:abcd1234ef/1.23 at 172.1.2.3:80\) has no hardware version",
    ):
        del data["hv"]
        Box(mock_session, data, config, None)


async def test_without_api_level(mock_session, data, config):
    with pytest.raises(
        error.UnsupportedBoxVersion,
        match=r"unsupported version",
    ):
        del data["apiLevel"]
        Box._match_device_config(data)


async def test_with_init_failure(mock_session, data, config):
    with patch(
        "blebox_uniapi.box.AirQuality.many_from_config", spec_set=True, autospec=True
    ) as mock_sensor:
        mock_sensor.side_effect = KeyError
        with pytest.raises(
            error.UnsupportedBoxResponse,
            match=r"Failed to initialize:",
        ):
            Box(mock_session, data, config, None)


async def test_properties(mock_session, data, config):
    box = Box(mock_session, data, config, None)
    assert "foobar" == box.name
    assert None is box.last_data
    assert "airSensor" == box.type
    assert "airSensor" == box.model
    assert "abcd1234ef" == box.unique_id
    assert "1.23" == box.firmware_version
    assert "4.56" == box.hardware_version
    assert "BleBox" == box.brand
    assert 20180403 == box.api_version


async def test_validations(mock_session, data, config):
    box = Box(mock_session, data, config, None)

    with pytest.raises(
        error.BadFieldExceedsMax,
        match=r"foobar.field1 is 123 which exceeds max \(100\)",
    ):
        box.check_int_range(123, "field1", 100, 0)

    with pytest.raises(
        error.BadFieldLessThanMin,
        match=r"foobar.field1 is 123 which is less than minimum \(200\)",
    ):
        box.check_int_range(123, "field1", 300, 200)

    with pytest.raises(error.BadFieldMissing, match=r"foobar.field1 is missing"):
        box.check_int(None, "field1", 300, 200)

    with pytest.raises(
        error.BadFieldNotANumber, match=r"foobar.field1 is '123' which is not a number"
    ):
        box.check_int("123", "field1", 300, 200)

    with pytest.raises(error.BadFieldMissing, match=r"foobar.field1 is missing"):
        box.check_hex_str(None, "field1", 300, 200)

    with pytest.raises(
        error.BadFieldNotAString, match=r"foobar.field1 is 123 which is not a string"
    ):
        box.check_hex_str(123, "field1", 300, 200)

    with pytest.raises(error.BadFieldMissing, match=r"foobar.field1 is missing"):
        box.check_rgbw(None, "field1")

    with pytest.raises(
        error.BadFieldNotAString, match=r"foobar.field1 is 123 which is not a string"
    ):
        box.check_rgbw(123, "field1")

    with pytest.raises(
        error.BadFieldNotRGBW, match=r"foobar.field1 is 123 which is not a rgbw string"
    ):
        box.check_rgbw("123", "field1")
