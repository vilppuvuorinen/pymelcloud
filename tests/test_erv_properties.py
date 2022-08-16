"""ERV tests."""
import json
import os

import pytest
from asynctest import CoroutineMock, Mock, patch
from pymelcloud import DEVICE_TYPE_ERV
from pymelcloud.erv_device import (
    VENTILATION_MODE_AUTO,
    VENTILATION_MODE_BYPASS,
    VENTILATION_MODE_RECOVERY,
    ErvDevice,
)


def _build_device(device_conf_name: str, device_state_name: str) -> ErvDevice:
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
        _client.fetch_energy_report = CoroutineMock(return_value=None)
        client = _client

    return ErvDevice(device_conf, client)

@pytest.mark.asyncio
async def test_erv():
    device = _build_device("erv_listdevice.json", "erv_get.json")

    assert device.name == ""
    assert device.device_type == DEVICE_TYPE_ERV
    assert device.temperature_increment == 1.0
    assert device.has_energy_consumed_meter is True
    assert device.total_energy_consumed == 0.1
    assert device.room_temperature is None
    assert device.outside_temperature is None
    assert device.room_co2_level is None

    assert device.ventilation_mode is None
    assert device.ventilation_modes == [
        VENTILATION_MODE_RECOVERY,
        VENTILATION_MODE_BYPASS,
        VENTILATION_MODE_AUTO,
    ]
    assert device.actual_ventilation_mode is None
    assert device.fan_speed is None
    assert device.fan_speeds is None
    assert device.actual_supply_fan_speed is None
    assert device.actual_exhaust_fan_speed is None
    assert device.core_maintenance_required is False
    assert device.filter_maintenance_required is False
    assert device.night_purge_mode is False

    await device.update()

    assert device.room_temperature == 29.0
    assert device.outside_temperature == 28.0
    assert device.room_co2_level is None

    assert device.ventilation_mode == VENTILATION_MODE_RECOVERY
    assert device.actual_ventilation_mode == VENTILATION_MODE_RECOVERY
    assert device.fan_speed == "3"
    assert device.fan_speeds == ["1", "2", "3", "4"]
    assert device.actual_supply_fan_speed == "3"
    assert device.actual_exhaust_fan_speed == "3"
    assert device.core_maintenance_required is False
    assert device.filter_maintenance_required is False
    assert device.night_purge_mode is False

    assert device.wifi_signal == -65
    assert device.has_error is False
    assert device.error_code == 8000
    assert str(device.last_seen) == '2020-07-07 06:44:11.027000+00:00'
