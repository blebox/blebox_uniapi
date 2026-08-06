from unittest.mock import Mock
import pytest

from blebox_uniapi.button import Button
from blebox_uniapi.box import Box
from blebox_uniapi.box_types import BOX_TYPE_CONF, get_latest_api_level
from blebox_uniapi.cover import GateBoxControlType, GateBoxExtraButtonType

from .conftest import CommonEntity, DefaultBoxTest, future_date


class BleBoxButtonEntity(CommonEntity):
    async def async_press(self):
        return await self._feature.set()


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


def gate_box_buttons(product: Box, extended_state) -> list[Button]:
    product.type = "gateBox"
    return Button.many_from_config(
        product,
        BOX_TYPE_CONF["gateBox"][20200831]["buttons"],
        extended_state=extended_state,
    )


@pytest.fixture
def gate_box_second_output(product: Box) -> Button:
    many = gate_box_buttons(
        product,
        {
            "gate": {
                "extraButtonType": GateBoxExtraButtonType.WALK_IN,
                "openCloseMode": GateBoxControlType.STEP_BY_STEP,
            }
        },
    )
    assert len(many) == 1
    return many[0]


async def test_gate_box_second_output_pressed(
    gate_box_second_output: Button, product: Box
):
    await gate_box_second_output.set()
    product.async_api_command.assert_called_with("secondary", "second_output")


def test_gate_box_second_output_alias(gate_box_second_output: Button):
    assert gate_box_second_output.alias == "second_output"
    assert gate_box_second_output.control_type is None


@pytest.mark.parametrize(
    "extra_button_type",
    [GateBoxExtraButtonType.WALK_IN, GateBoxExtraButtonType.OTHER],
)
@pytest.mark.parametrize(
    "open_close_mode",
    [GateBoxControlType.STEP_BY_STEP, GateBoxControlType.ONLY_OPEN],
)
def test_gate_box_second_output_created(
    product: Box,
    extra_button_type: GateBoxExtraButtonType,
    open_close_mode: GateBoxControlType,
):
    many = gate_box_buttons(
        product,
        {
            "gate": {
                "extraButtonType": extra_button_type,
                "openCloseMode": open_close_mode,
            }
        },
    )
    assert len(many) == 1


@pytest.mark.parametrize(
    "extra_button_type",
    [GateBoxExtraButtonType.WALK_IN, GateBoxExtraButtonType.OTHER],
)
def test_gate_box_second_output_created_without_open_close_mode(
    product: Box, extra_button_type: GateBoxExtraButtonType
):
    """Test api levels below 20230102, which never report openCloseMode."""

    many = gate_box_buttons(product, {"gate": {"extraButtonType": extra_button_type}})
    assert len(many) == 1


@pytest.mark.parametrize(
    "gate",
    [
        {
            "extraButtonType": GateBoxExtraButtonType.WALK_IN,
            "openCloseMode": GateBoxControlType.OPEN_CLOSE,
        },
        {
            "extraButtonType": GateBoxExtraButtonType.OTHER,
            "openCloseMode": GateBoxControlType.OPEN_CLOSE,
        },
        {
            "extraButtonType": GateBoxExtraButtonType.DISABLED,
            "openCloseMode": GateBoxControlType.STEP_BY_STEP,
        },
        {
            "extraButtonType": GateBoxExtraButtonType.STOP,
            "openCloseMode": GateBoxControlType.STEP_BY_STEP,
        },
        {"extraButtonType": GateBoxExtraButtonType.DISABLED},
        {"extraButtonType": GateBoxExtraButtonType.STOP},
        {"openCloseMode": GateBoxControlType.STEP_BY_STEP},
        {},
    ],
)
def test_gate_box_second_output_not_created(product: Box, gate: dict):
    assert gate_box_buttons(product, {"gate": gate}) == []


@pytest.mark.parametrize(
    ("box_type", "api_level"), [("gateBox", 20200831), ("tvLiftBox", 20200518)]
)
@pytest.mark.parametrize("extended_state", [None, {}, "not a dict"])
def test_no_buttons_without_usable_extended_state(
    product: Box, box_type: str, api_level: int, extended_state
):
    product.type = box_type
    many = Button.many_from_config(
        product,
        BOX_TYPE_CONF[box_type][api_level]["buttons"],
        extended_state=extended_state,
    )
    assert many == []


class TestGateBoxSecondOutput(DefaultBoxTest):
    """Tests for a gateBox exposing its extra button output as a button."""

    DEVCLASS = "buttons"
    ENTITY_CLASS = BleBoxButtonEntity
    DEV_INFO_PATH = "state/extended"

    DEVICE_INFO = {
        "device": {
            "deviceName": "My gateBox 1",
            "type": "gateBox",
            "product": "gateBox",
            "fv": "0.1010",
            "hv": "9.1d",
            "id": "1afe34d27e4f",
            "apiLevel": "20230102",
        }
    }
    DEVICE_INFO_FUTURE = {
        "device": {**DEVICE_INFO["device"], "apiLevel": future_date()}
    }
    DEVICE_INFO_LATEST = {
        "device": {
            **DEVICE_INFO["device"],
            "apiLevel": get_latest_api_level("gateBox"),
        }
    }
    DEVICE_INFO_UNSUPPORTED = DEVICE_INFO
    DEVICE_INFO_UNSPECIFIED_API = None  # already handled as default case

    STATE_DEFAULT = {
        "gate": {
            "currentPos": 0,
            "openCloseMode": 0,
            "gateType": 1,
            "gatePulseTimeMs": 1500,
            "gateOutputState": 0,
            "extraButtonType": 2,
            "extraButtonPulseTimeMs": 1500,
            "extraButtonOutputState": 0,
            "inputsType": 0,
        }
    }
    DEVICE_EXTENDED_INFO = STATE_DEFAULT
    DEVICE_EXTENDED_INFO_PATH = "/state/extended"

    async def test_init(self, aioclient_mock):
        """Test that a usable extra button output yields exactly one button."""

        await self.allow_get_info(aioclient_mock)
        entities = await self.async_entities(aioclient_mock)

        assert len(entities) == 1
        entity = entities[0]
        assert entity.name == "My gateBox 1 (gateBox#second_output)"
        assert entity.unique_id == "BleBox-gateBox-1afe34d27e4f-second_output"

    async def test_pressed(self, aioclient_mock):
        """Test that pressing the button pulses the extra button output."""

        await self.allow_get_info(aioclient_mock)
        entity = (await self.async_entities(aioclient_mock))[0]

        self.allow_get(aioclient_mock, "/s/s", self.STATE_DEFAULT)
        await entity.async_press()


class TestGateBoxSecondOutputWithoutOpenCloseMode(TestGateBoxSecondOutput):
    """Tests for a gateBox on an api level that never reports openCloseMode."""

    DEVICE_INFO = {
        "device": {
            **TestGateBoxSecondOutput.DEVICE_INFO["device"],
            "apiLevel": "20220713",
        }
    }
    DEVICE_INFO_UNSUPPORTED = DEVICE_INFO

    STATE_DEFAULT = {
        "gate": {
            "currentPos": 0,
            "gateType": 1,
            "gatePulseTimeMs": 1500,
            "extraButtonType": 2,
            "extraButtonPulseTimeMs": 1500,
        }
    }
    DEVICE_EXTENDED_INFO = STATE_DEFAULT
