from unittest.mock import Mock
import pytest

from blebox_uniapi.button import Button
from blebox_uniapi.box import Box
from blebox_uniapi.box_types import BOX_TYPE_CONF


@pytest.fixture
def product():
    return Mock(spec=Box)


@pytest.fixture
def tv_lift_box_0(product):
    product.type = "tvLiftBox"
    extended_state = {"tvLift": {"controlType": 4}}
    many = Button.many_from_config(
        product,
        BOX_TYPE_CONF["tvLiftBox"][20200518]["buttons"],
        extended_state=extended_state,
    )
    assert len(many) == 3
    return many[0]


@pytest.fixture
def tv_lift_box_1(product):
    product.type = "tvLiftBox"
    extended_state = {"tvLift": {"controlType": 4}}
    many = Button.many_from_config(
        product,
        BOX_TYPE_CONF["tvLiftBox"][20200518]["buttons"],
        extended_state=extended_state,
    )
    assert len(many) == 3
    return many[1]


async def test_tv_lift_0_box_pressed(tv_lift_box_0: Button, product: Box):
    await tv_lift_box_0.set()
    product.async_api_command.assert_called_with("set", "open_or_stop")
    assert tv_lift_box_0.control_type


async def test_tv_lift_1_box_pressed(tv_lift_box_1: Button, product: Box):
    await tv_lift_box_1.set()
    product.async_api_command.assert_called_with("set", "close_or_stop")
    assert tv_lift_box_1.control_type
