from unittest.mock import Mock
from blebox_uniapi.box_types import BOX_TYPE_CONF
import pytest

from blebox_uniapi.error import BadOnValueError
from blebox_uniapi.light import Light
from blebox_uniapi.box import Box


@pytest.fixture
def product():
    return Mock(spec=Box)


@pytest.fixture
def dimmer_box(product):
    product.type = "dimmerBox"
    many = Light.many_from_config(
        product, BOX_TYPE_CONF["dimmerBox"][20170829]["lights"], extended_state={}
    )
    assert len(many) == 1
    return many[0]


@pytest.fixture
def w_light_box_rgbww(product):
    product.type = "wLightBox"
    extended_state = {
        "rgbw": {
            "colorMode": 7,
            "effectID": 0,
            "desiredColor": "fcfffcff00",
            "currentColor": "fcfffcff00",
            "lastOnColor": "fcfffcff00",
            "durationsMs": {"colorFade": 1000, "effectFade": 1000, "effectStep": 1000},
            "favColors": {"0": "ff", "1": "00", "2": "c0", "3": "40", "4": "00"},
            "effectsNames": {"0": "NONE", "1": "FADE", "2": "Stroboskop", "3": "BELL"},
        }
    }
    many = Light.many_from_config(
        product,
        BOX_TYPE_CONF["wLightBox"][20200229]["lights"],
        extended_state=extended_state,
    )
    return many[0]


@pytest.mark.parametrize("input_on", range(1, 255))
async def test_dimmer_box_async_on_with_int(dimmer_box: Light, product: Mock, input_on):
    await dimmer_box.async_on(input_on)
    product.async_api_command.assert_called_with("set", input_on)


async def test_dimmer_box_async_on_zero(dimmer_box: Light, product: Mock):
    with pytest.raises(BadOnValueError):
        await dimmer_box.async_on(0)


async def test_dimmer_box_async_on_with_hex(dimmer_box: Light, product: Mock):
    await dimmer_box.async_on("ff")
    product.async_api_command.assert_called_with("set", 255)


@pytest.mark.parametrize("input_on", [255, "ff"])
async def test_dimmer_box_async_on(dimmer_box: Light, product: Mock, input_on):
    await dimmer_box.async_on(input_on)
    product.async_api_command.assert_called_with("set", 255)


async def test_dimmer_box_async_off(dimmer_box: Light, product: Mock):
    await dimmer_box.async_off()
    product.async_api_command.assert_called_with("set", 0)


@pytest.mark.parametrize(
    "io_params",
    [("ff", [255]), ("ffff", [255, 255]), ("ff14cdfe6a", [255, 20, 205, 254, 106])],
)
def test_dimmer_box_rgb_hex_to_rgb_list(dimmer_box: Light, io_params):
    assert dimmer_box.rgb_hex_to_rgb_list(io_params[0]) == io_params[1]


@pytest.mark.parametrize(
    "io_params",
    [
        (["ff"], [255]),
        (["ff", "ff"], [255, 255]),
        (["ff", "14", "cd", "fe", "6a"], [255, 20, 205, 254, 106]),
    ],
)
def test_dimmer_box_rgb_list_to_rgb_hex_list(dimmer_box: Light, io_params):
    assert dimmer_box.rgb_list_to_rgb_hex_list(io_params[1]) == io_params[0]


@pytest.mark.parametrize(
    "io_params",
    [
        ([255], [255]),
        ([255, 255], [255, 255]),
        ([120, 20, 205, 96, 106], [149, 25, 255, 119, 132]),
    ],
)
def test_dimmer_box_normalise_elements_of_rgb(dimmer_box: Light, io_params):
    assert dimmer_box.normalise_elements_of_rgb(io_params[0]) == io_params[1]


def test_dimmer_box_normalise_elements_of_rgb_(dimmer_box: Light):
    with pytest.raises(BadOnValueError):
        dimmer_box.normalise_elements_of_rgb([-10])

    with pytest.raises(BadOnValueError):
        dimmer_box.normalise_elements_of_rgb([256])

    with pytest.raises(BadOnValueError):
        dimmer_box.normalise_elements_of_rgb([-1, 0])


@pytest.mark.parametrize(
    "io_params", [([145, 135, 90], 145), ([145, 135, 240], 240), ([255], 255)]
)
def test_dimmer_box_evaluate_brightness_from_rgb(dimmer_box: Light, io_params):
    assert dimmer_box.evaluate_brightness_from_rgb(io_params[0]) == io_params[1]


def test_dimmer_box_apply_brightness_zero(dimmer_box: Light):
    assert dimmer_box.apply_brightness(10, 0) == [0]


def test_dimmer_box_evaluate_brightness_from_rgb_out_of_range(dimmer_box: Light):
    with pytest.raises(BadOnValueError):
        dimmer_box.evaluate_brightness_from_rgb([257, 135, 90])

    with pytest.raises(BadOnValueError):
        dimmer_box.evaluate_brightness_from_rgb([145, 135, -1])

    with pytest.raises(BadOnValueError):
        dimmer_box.evaluate_brightness_from_rgb([145, -10, 900])


def test_light_sensible_on_value_last_is_zero(w_light_box_rgbww: Light):
    assert len(w_light_box_rgbww.effect_list) == 4
    assert w_light_box_rgbww.effect == "NONE"
