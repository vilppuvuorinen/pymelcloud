"""MELCloud module"""
from datetime import timedelta
from typing import Dict, List, Optional

from aiohttp import ClientSession

from pymelcloud.ata_device import AtaDevice
from pymelcloud.atw_device import AtwDevice
from pymelcloud.client import Client as _Client
from pymelcloud.client import login as _login
from pymelcloud.device import Device

DEVICE_TYPE_ATA = "ata"
DEVICE_TYPE_ATW = "atw"


async def login(
    email: str,
    password: str,
    session: Optional[ClientSession] = None,
    *,
    conf_update_interval: Optional[timedelta] = timedelta(minutes=5),
    device_set_debounce: Optional[timedelta] = timedelta(seconds=1),
) -> str:
    """
    Log in to MELCloud with given credentials.
    
    Returns access token.
    """
    _client = await _login(
        email,
        password,
        session,
        conf_update_interval=conf_update_interval,
        device_set_debounce=device_set_debounce,
    )
    return _client.token


async def get_devices(
    token: str,
    session: Optional[ClientSession] = None,
    *,
    conf_update_interval=timedelta(minutes=5),
    device_set_debounce=timedelta(seconds=1),
) -> Dict[str, List[Device]]:
    """Initialize Devices available with the token."""
    _client = _Client(
        token,
        session,
        conf_update_interval=conf_update_interval,
        device_set_debounce=device_set_debounce,
    )
    await _client.update_confs()
    return {
        DEVICE_TYPE_ATA: [
            AtaDevice(conf, _client, set_debounce=device_set_debounce)
            for conf in _client.device_confs
            if conf.get("Device", {}).get("DeviceType") == 0
        ],
        DEVICE_TYPE_ATW: [
            AtwDevice(conf, _client, set_debounce=device_set_debounce)
            for conf in _client.device_confs
            if conf.get("Device", {}).get("DeviceType") == 1
        ],
    }
