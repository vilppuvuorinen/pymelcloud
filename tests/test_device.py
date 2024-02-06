"""Device tests."""
from typing import Any, Dict, Optional

import pytest
from pymelcloud.ata_device import AtaDevice
from .util import build_device


def _build_device(device_conf_name: str, device_state_name: str, energy_report: Optional[Dict[Any, Any]]=None) -> AtaDevice:
    device_conf, client = build_device(device_conf_name, device_state_name, energy_report)
    return AtaDevice(device_conf, client)


@pytest.mark.asyncio
async def test_round_temperature():
    device = _build_device("ata_listdevice.json", "ata_get.json")
    device._device_conf.get("Device")["TemperatureIncrement"] = 0.5

    assert device.round_temperature(23.99999) == 24.0
    assert device.round_temperature(24.0) == 24.0
    assert device.round_temperature(24.00001) == 24.0
    assert device.round_temperature(24.24999) == 24.0
    assert device.round_temperature(24.25) == 24.5
    assert device.round_temperature(24.25001) == 24.5
    assert device.round_temperature(24.5) == 24.5
    assert device.round_temperature(24.74999) == 24.5
    assert device.round_temperature(24.75) == 25.0
    assert device.round_temperature(24.75001) == 25.0

    device._device_conf.get("Device")["TemperatureIncrement"] = 1

    assert device.round_temperature(23.99999) == 24.0
    assert device.round_temperature(24.0) == 24.0
    assert device.round_temperature(24.00001) == 24.0
    assert device.round_temperature(24.49999) == 24.0
    assert device.round_temperature(24.5) == 25.0
    assert device.round_temperature(24.50001) == 25.0
    assert device.round_temperature(25.0) == 25.0
    assert device.round_temperature(25.00001) == 25.0
    assert device.round_temperature(25.49999) == 25.0
    assert device.round_temperature(25.5) == 26.0
