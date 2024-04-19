import pytest
from unittest import mock
from blebox_uniapi.box import Box
from blebox_uniapi import error
from blebox_uniapi.jfollow import follow

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_session():
    return mock.MagicMock(host="172.1.2.3", port=80)


@pytest.fixture
def sample_data():
    return {
        "id": "abcd1234ef",
        "type": "airSensor",
        "deviceName": "foobar",
        "fv": "1.23",
        "hv": "4.56",
        "apiLevel": "20180403",
    }


@pytest.fixture
def config(sample_data):
    return Box._match_device_config(sample_data)


async def test_without_type(mock_session, sample_data, config):
    del sample_data["type"]

    with pytest.raises(error.UnsupportedBoxResponse, match="has no type"):
        Box(mock_session, sample_data, config, None)


async def test_with_unknown_type(mock_session, sample_data):
    sample_data["type"] = "unknownBox"

    with pytest.raises(error.UnsupportedBoxResponse, match="not a supported type"):
        Box._match_device_config(sample_data)


async def test_without_name(mock_session, sample_data, config):
    del sample_data["deviceName"]

    with pytest.raises(error.UnsupportedBoxResponse, match="has no name"):
        Box(mock_session, sample_data, config, None)


async def test_without_firmware_version(mock_session, sample_data, config):
    del sample_data["fv"]

    with pytest.raises(error.UnsupportedBoxResponse, match="has no firmware version"):
        Box(mock_session, sample_data, config, None)


async def test_without_hardware_version(mock_session, sample_data, config):
    del sample_data["hv"]

    with pytest.raises(error.UnsupportedBoxResponse, match="has no hardware version"):
        Box(mock_session, sample_data, config, None)


async def test_without_api_level(mock_session, sample_data, config):
    del sample_data["apiLevel"]

    with pytest.raises(error.UnsupportedBoxVersion, match=r"unsupported version"):
        Box._match_device_config(sample_data)


async def test_json_path_extraction(mock_session, sample_data, config):
    # note: follow is thin wrapper over jmespath so there's no real reason to test it.
    # However, this tests makes sure we understand the syntax and know how it works.
    # We can also use it as a canary for any unexpected change in syntax that may come
    # in newer version.

    # succesfull extraction
    assert follow(["foo"], "[0]") == "foo"
    assert follow([{"foo": "3", "value": 4}], "[?foo=='3'].value") == [4]

    # "dud" extraction
    assert follow([{"foo": "ab", "value": 4}], "[?foo=='bc'].value") == []
    assert follow([{"value": 4}], "[1].value") is None
    assert follow({"value": 4}, "foo") is None
    assert follow({"foo": [4]}, "[?bar==`0`].value") is None


async def test_missing_device_id(mock_session, sample_data, config):
    del sample_data["id"]
    with pytest.raises(error.UnsupportedBoxResponse, match="has no id"):
        Box(mock_session, sample_data, config, None)


# Add more test cases for other missing fields (type, name, versions, etc.)


async def test_invalid_init(mock_session, sample_data, config):
    with mock.patch(
        "blebox_uniapi.sensor.SensorFactory.many_from_config",
        spec_set=True,
        autospec=True,
    ) as mock_sensor:
        mock_sensor.side_effect = KeyError
        with pytest.raises(
            error.UnsupportedBoxResponse, match=r"Failed to initialize:"
        ):
            Box(mock_session, sample_data, config, None)


async def test_properties(mock_session, sample_data, config):
    box = Box(mock_session, sample_data, config, None)
    assert box.name == "foobar"
    assert box.last_data is None
    assert box.type == "airSensor"
    assert box.model == "airSensor"
    assert box.unique_id == "abcd1234ef"
    assert box.firmware_version == "1.23"
    assert box.hardware_version == "4.56"
    assert box.brand == "BleBox"
    assert box.api_version == 20180403
    assert box.address == "172.1.2.3:80"


async def test_field_validations(mock_session, sample_data, config):
    box = Box(mock_session, sample_data, config, None)

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
