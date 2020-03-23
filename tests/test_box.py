import json

import pytest

from unittest import mock

from asynctest import patch

from blebox_uniapi.box import Box
from blebox_uniapi import error


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


def test_json_paths(mock_session, data):
    box = Box(mock_session, data)

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


def test_without_id(mock_session, data):
    with pytest.raises(
        error.UnsupportedBoxResponse, match="Device at 172.1.2.3:80 has no id"
    ):
        del data["id"]
        Box(mock_session, data)


def test_without_type(mock_session, data):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match="Device:abcd1234ef at 172.1.2.3:80 has no type",
    ):
        del data["type"]
        Box(mock_session, data)


def test_with_unknown_type(mock_session, data):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match="unknownBox:abcd1234ef at 172.1.2.3:80 is not a supported type",
    ):
        data["type"] = "unknownBox"
        Box(mock_session, data)


def test_without_name(mock_session, data):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match="airSensor:abcd1234ef at 172.1.2.3:80 has no name",
    ):
        del data["deviceName"]
        Box(mock_session, data)


def test_without_firmware_version(mock_session, data):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match=r"'foobar' \(airSensor:abcd1234ef at 172.1.2.3:80\) has no firmware version",
    ):
        del data["fv"]
        Box(mock_session, data)


def test_without_hardware_version(mock_session, data):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match=r"'foobar' \(airSensor:abcd1234ef/1.23 at 172.1.2.3:80\) has no hardware version",
    ):
        del data["hv"]
        Box(mock_session, data)


def test_without_api_level(mock_session, data):
    with pytest.raises(
        error.UnsupportedBoxResponse,
        match=r"'foobar' \(airSensor:abcd1234ef/1.23 at 172.1.2.3:80\) has no apiLevel",
    ):
        del data["apiLevel"]
        Box(mock_session, data)

def test_with_init_failure(mock_session, data):
    with patch("blebox_uniapi.box.AirQuality", spec_set=True, autospec=True) as mock_sensor:
        mock_sensor.side_effect=KeyError
        with pytest.raises(
            error.UnsupportedBoxResponse,
            match=r"'foobar' \(airSensor:abcd1234ef/1.23 at 172.1.2.3:80\) failed to initialize: ",
        ):
            Box(mock_session, data)


def test_properties(mock_session, data):
    box = Box(mock_session, data)
    assert "foobar" == box.name
    assert None is box.last_data
    assert "airSensor" == box.type
    assert "abcd1234ef" == box.unique_id
    assert "1.23" == box.firmware_version
    assert "4.56" == box.hardware_version
    assert 20180403 == box.api_version
    assert (1, 0, 0) == box.version
    assert True is box.outdated

def test_validations(mock_session, data):
    box = Box(mock_session, data)

    with pytest.raises(error.BadFieldExceedsMax, match=r"foobar.field1 is 123 which exceeds max \(100\)"):
        box.check_int_range(123, "field1", 100, 0)

    with pytest.raises(error.BadFieldLessThanMin, match=r"foobar.field1 is 123 which is less than minimum \(200\)"):
        box.check_int_range(123, "field1", 300, 200)

    with pytest.raises(error.BadFieldMissing, match=r"foobar.field1 is missing"):
        box.check_int(None, "field1", 300, 200)

    with pytest.raises(error.BadFieldNotANumber, match=r"foobar.field1 is '123' which is not a number"):
        box.check_int("123", "field1", 300, 200)



    with pytest.raises(error.BadFieldMissing, match=r"foobar.field1 is missing"):
        box.check_hex_str(None, "field1", 300, 200)

    with pytest.raises(error.BadFieldNotAString, match=r"foobar.field1 is 123 which is not a string"):
        box.check_hex_str(123, "field1", 300, 200)



    with pytest.raises(error.BadFieldMissing, match=r"foobar.field1 is missing"):
        box.check_rgbw(None, "field1")

    with pytest.raises(error.BadFieldNotAString, match=r"foobar.field1 is 123 which is not a string"):
        box.check_rgbw(123, "field1")

    with pytest.raises(error.BadFieldNotRGBW, match=r"foobar.field1 is 123 which is not a rgbw string"):
        box.check_rgbw("123", "field1")
