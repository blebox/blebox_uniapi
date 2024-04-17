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

# async def test_json_path_extraction(mock_session, sample_data, config):
#     box = Box(mock_session, sample_data, config, None)

#     # Test valid JSON path extraction
#     assert follow(["foo"], "[0]") == "foo"
#     assert follow([{"foo": "3", "value": 4}], "[?foo=='3'].value") == [4]

#     # Test JSON path extraction with non-matching condition
#     with pytest.raises(error.JPathFailed, match=r"with: foo=bc at .* within .*"):
#         follow([{"foo": "ab", "value": 4}], "[?foo=='bc'].value")

#     # Test JSON path extraction errors
#     with pytest.raises(error.JPathFailed, match=r"with value at index 1 at .* within .*"):
#         follow([{"value": 4}], "[1].value")

#     with pytest.raises(error.JPathFailed, match=r"item 'foo' not among \['value'\] at .* within .*"):
#         follow({"value": 4}, "foo")

#     with pytest.raises(error.JPathFailed, match=r"list expected but got {'foo': \[4\]} at .* within .*"):
#         follow({"foo": [4]}, "[?bar==`0`].value")

async def test_missing_device_id(mock_session, sample_data, config):
    del sample_data["id"]
    with pytest.raises(error.UnsupportedBoxResponse, match="Device at 172.1.2.3:80 has no id"):
        Box(mock_session, sample_data, config, None)

# Add more test cases for other missing fields (type, name, versions, etc.)

async def test_invalid_init(mock_session, sample_data, config):
    with mock.patch(
        "blebox_uniapi.sensor.SensorFactory.many_from_config",
        spec_set=True,
        autospec=True,
    ) as mock_sensor:
        mock_sensor.side_effect = KeyError
        with pytest.raises(error.UnsupportedBoxResponse, match=r"Failed to initialize:"):
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
