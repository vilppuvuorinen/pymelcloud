"""ATA tests."""
import json
import os

import pytest
from asynctest import CoroutineMock, Mock, patch
from pymelcloud import DEVICE_TYPE_ATA
from pymelcloud.ata_device import (
    OPERATION_MODE_HEAT,
    OPERATION_MODE_DRY,
    OPERATION_MODE_COOL,
    OPERATION_MODE_FAN_ONLY,
    OPERATION_MODE_HEAT_COOL,
    V_VANE_POSITION_AUTO,
    V_VANE_POSITION_1,
    V_VANE_POSITION_2,
    V_VANE_POSITION_3,
    V_VANE_POSITION_4,
    V_VANE_POSITION_5,
    V_VANE_POSITION_SWING,
    V_VANE_POSITION_UNDEFINED,
    H_VANE_POSITION_AUTO,
    H_VANE_POSITION_1,
    H_VANE_POSITION_2,
    H_VANE_POSITION_3,
    H_VANE_POSITION_4,
    H_VANE_POSITION_5,
    H_VANE_POSITION_SPLIT,
    H_VANE_POSITION_SWING,
    H_VANE_POSITION_UNDEFINED,
    AtaDevice,
)


def _build_device(device_conf_name: str, device_state_name: str) -> AtaDevice:
    test_dir = os.path.join(os.path.dirname(__file__), "samples")
    with open(os.path.join(test_dir, device_conf_name), "r") as json_file:
        device_conf = json.load(json_file)

    with open(os.path.join(test_dir, device_state_name), "r") as json_file:
        device_state = json.load(json_file)

    with patch("pymelcloud.client.Client") as _client:
        _client.update_confs = CoroutineMock()
        _client.device_confs.__iter__ = Mock(return_value=[device_conf].__iter__())
        _client.fetch_device_units = CoroutineMock(return_value=[])
        _client.fetch_device_state = CoroutineMock(return_value=device_state)
        client = _client

    return AtaDevice(device_conf, client)

@pytest.mark.asyncio
async def test_ata():
    device = _build_device("ata_listdevice.json", "ata_get.json")

    assert device.name == ""
    assert device.device_type == DEVICE_TYPE_ATA
    assert device.temperature_increment == 0.5
    assert device.has_energy_consumed_meter is False
    assert device.room_temperature is None

    assert device.operation_modes == [
        OPERATION_MODE_HEAT,
        OPERATION_MODE_DRY,
        OPERATION_MODE_COOL,
        OPERATION_MODE_FAN_ONLY,
        OPERATION_MODE_HEAT_COOL,
    ]
    assert device.fan_speed is None
    assert device.fan_speeds is None

    await device.update()

    assert device.room_temperature == 28.0
    assert device.target_temperature == 22.0

    assert device.operation_mode == OPERATION_MODE_COOL
    assert device.fan_speed == "3"
    assert device.actual_fan_speed == "0"
    assert device.fan_speeds == ["auto", "1", "2", "3", "4", "5"]
    
    assert device.vane_vertical == V_VANE_POSITION_AUTO
    assert device.vane_horizontal == H_VANE_POSITION_3

    assert device.wifi_signal == -51
    assert device.has_error is False
    assert device.error_code == 8000
    
