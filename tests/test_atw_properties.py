"""Ecodan tests."""
import pytest
from pymelcloud import DEVICE_TYPE_ATW
from pymelcloud.atw_device import (
    OPERATION_MODE_AUTO,
    OPERATION_MODE_FORCE_HOT_WATER,
    STATUS_HEAT_WATER,
    STATUS_HEAT_ZONES,
    STATUS_UNKNOWN,
    ZONE_OPERATION_MODE_COOL,
    ZONE_OPERATION_MODE_HEAT,
    ZONE_STATUS_HEAT,
    ZONE_STATUS_IDLE,
    ZONE_STATUS_UNKNOWN,
    AtwDevice,
)
from .util import build_device


def _build_device(device_conf_name: str, device_state_name: str) -> AtwDevice:
    device_conf, client = build_device(device_conf_name, device_state_name)
    return AtwDevice(device_conf, client)


@pytest.mark.asyncio
async def test_1zone():
    device = _build_device("atw_1zone_listdevice.json", "atw_1zone_get.json")

    assert device.name == "Heater and Water"
    assert device.device_type == DEVICE_TYPE_ATW
    assert device.temperature_increment == 0.5

    assert device.operation_mode is None
    assert device.operation_modes == [
        OPERATION_MODE_AUTO,
        OPERATION_MODE_FORCE_HOT_WATER,
    ]
    assert device.tank_temperature is None
    assert device.status is STATUS_UNKNOWN
    assert device.target_tank_temperature is None
    assert device.target_tank_temperature_min == 40
    assert device.target_tank_temperature_max == 60
    assert device.holiday_mode is None

    zones = device.zones

    assert len(zones) == 1
    assert zones[0].name == "Zone 1"
    assert zones[0].zone_index == 1
    assert zones[0].room_temperature is None
    assert zones[0].target_temperature is None
    assert zones[0].flow_temperature == 57.5
    assert zones[0].return_temperature == 53.0
    assert zones[0].target_flow_temperature is None
    assert zones[0].operation_mode is None
    assert zones[0].operation_modes == [ZONE_OPERATION_MODE_HEAT]
    assert zones[0].status == ZONE_STATUS_UNKNOWN

    await device.update()

    assert device.operation_mode == OPERATION_MODE_AUTO
    assert device.status == STATUS_HEAT_ZONES
    assert device.tank_temperature == 52.0
    assert device.target_tank_temperature == 50.0
    assert device.holiday_mode is False

    assert zones[0].room_temperature == 27.0
    assert zones[0].target_temperature == 30
    assert zones[0].target_flow_temperature == 60.0
    assert zones[0].operation_mode == ZONE_OPERATION_MODE_HEAT
    assert zones[0].operation_modes == [ZONE_OPERATION_MODE_HEAT]
    assert zones[0].status == ZONE_STATUS_HEAT


@pytest.mark.asyncio
async def test_2zone():
    device = _build_device("atw_2zone_listdevice.json", "atw_2zone_get.json")

    assert device.name == "Home"
    assert device.device_type == DEVICE_TYPE_ATW
    assert device.temperature_increment == 0.5

    assert device.operation_mode is None
    assert device.operation_modes == [
        OPERATION_MODE_AUTO,
        OPERATION_MODE_FORCE_HOT_WATER,
    ]
    assert device.tank_temperature is None
    assert device.status is STATUS_UNKNOWN
    assert device.target_tank_temperature is None
    assert device.target_tank_temperature_min == 40
    assert device.target_tank_temperature_max == 60
    assert device.holiday_mode is None

    zones = device.zones

    assert len(zones) == 2
    assert zones[0].name == "Downstairs"
    assert zones[0].zone_index == 1
    assert zones[0].room_temperature is None
    assert zones[0].target_temperature is None
    assert zones[0].flow_temperature == 36.0
    assert zones[0].return_temperature == 30.0
    assert zones[0].target_flow_temperature is None
    assert zones[0].operation_mode is None
    assert zones[0].operation_modes == [ZONE_OPERATION_MODE_HEAT]
    assert zones[0].status == ZONE_STATUS_UNKNOWN

    assert zones[1].name == "Upstairs"
    assert zones[1].zone_index == 2
    assert zones[1].room_temperature is None
    assert zones[1].target_temperature is None
    assert zones[1].flow_temperature == 36.0
    assert zones[1].return_temperature == 30.0
    assert zones[1].target_flow_temperature is None
    assert zones[1].operation_mode is None
    assert zones[1].operation_modes == [ZONE_OPERATION_MODE_HEAT]
    assert zones[1].status == ZONE_STATUS_UNKNOWN

    await device.update()

    assert device.operation_mode == OPERATION_MODE_AUTO
    assert device.status == STATUS_HEAT_ZONES
    assert device.tank_temperature == 49.5
    assert device.target_tank_temperature == 50.0
    assert device.holiday_mode is False

    assert zones[0].room_temperature == 20.5
    assert zones[0].target_temperature == 19.5
    assert zones[0].target_flow_temperature == 25.0
    assert zones[0].operation_mode == ZONE_OPERATION_MODE_HEAT
    assert zones[0].operation_modes == [ZONE_OPERATION_MODE_HEAT]
    assert zones[0].status == ZONE_STATUS_HEAT

    assert zones[1].room_temperature == 19.5
    assert zones[1].target_temperature == 18
    assert zones[1].target_flow_temperature == 25.0
    assert zones[1].operation_mode == ZONE_OPERATION_MODE_HEAT
    assert zones[1].operation_modes == [ZONE_OPERATION_MODE_HEAT]
    assert zones[1].status == ZONE_STATUS_HEAT


@pytest.mark.asyncio
async def test_2zone_cancool():
    device = _build_device(
        "atw_2zone_cancool_listdevice.json", "atw_2zone_cancool_get.json"
    )

    assert device.name == "Mitsubishi"
    assert device.device_type == DEVICE_TYPE_ATW
    assert device.temperature_increment == 0.5

    assert device.operation_mode is None
    assert device.operation_modes == [
        OPERATION_MODE_AUTO,
        OPERATION_MODE_FORCE_HOT_WATER,
    ]
    assert device.tank_temperature is None
    assert device.status is STATUS_UNKNOWN
    assert device.target_tank_temperature is None
    assert device.target_tank_temperature_min == 40
    assert device.target_tank_temperature_max == 60
    assert device.holiday_mode is None

    zones = device.zones

    assert len(zones) == 2
    assert zones[0].name == "Zone 1"
    assert zones[0].zone_index == 1
    assert zones[0].room_temperature is None
    assert zones[0].target_temperature is None
    assert zones[0].flow_temperature == 50.5
    assert zones[0].return_temperature == 50.5
    assert zones[0].target_flow_temperature is None
    assert zones[0].operation_mode is None
    assert zones[0].operation_modes == [
        ZONE_OPERATION_MODE_HEAT,
        ZONE_OPERATION_MODE_COOL,
    ]
    assert zones[0].status == ZONE_STATUS_UNKNOWN

    assert zones[1].name == "Zone 2"
    assert zones[1].zone_index == 2
    assert zones[1].room_temperature is None
    assert zones[1].target_temperature is None
    assert zones[1].flow_temperature == 50.5
    assert zones[1].return_temperature == 50.5
    assert zones[1].target_flow_temperature is None
    assert zones[1].operation_mode is None
    assert zones[1].operation_modes == [
        ZONE_OPERATION_MODE_HEAT,
        ZONE_OPERATION_MODE_COOL,
    ]
    assert zones[1].status == ZONE_STATUS_UNKNOWN

    await device.update()

    assert device.operation_mode == OPERATION_MODE_AUTO
    assert device.status == STATUS_HEAT_WATER
    assert device.tank_temperature == 47.5
    assert device.target_tank_temperature == 52.0
    assert device.holiday_mode is False

    assert zones[0].room_temperature == 21.5
    assert zones[0].target_temperature == 20.5
    assert zones[0].target_flow_temperature == 5.0
    assert zones[0].operation_mode == ZONE_OPERATION_MODE_HEAT
    assert zones[0].operation_modes == [
        ZONE_OPERATION_MODE_HEAT,
        ZONE_OPERATION_MODE_COOL,
    ]
    assert zones[0].status == ZONE_STATUS_IDLE

    assert zones[1].room_temperature == 21.0
    assert zones[1].target_temperature == 21.0
    assert zones[1].target_flow_temperature == 5.0
    assert zones[1].operation_mode == ZONE_OPERATION_MODE_HEAT
    assert zones[1].operation_modes == [
        ZONE_OPERATION_MODE_HEAT,
        ZONE_OPERATION_MODE_COOL,
    ]
    assert zones[1].status == ZONE_STATUS_IDLE
