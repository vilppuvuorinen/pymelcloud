"""MELCloud module"""
from aiohttp import ClientSession
import asyncio
from datetime import timedelta
from typing import List, Optional, Type

from pymelcloud.client import Client as _Client, login as _login
from pymelcloud.device import Device
from pymelcloud.atw_device import AtwDevice
from pymelcloud.ata_device import AtaDevice


async def login(
    email: str,
    password: str,
    session: Optional[ClientSession] = None,
    *,
    conf_update_interval: Optional[timedelta] = None,
    device_set_debounce: Optional[timedelta] = None,
) -> str:
    """
    Log in to MELCloud with given credentials.
    
    Returns access token.
    """
    client = await _login(
        email,
        password,
        session,
        conf_update_interval=timedelta(minutes=5),
        device_set_debounce=timedelta(seconds=1),
    )
    return client.token


async def get_devices(
    token: str,
    session: Optional[ClientSession] = None,
    *,
    conf_update_interval=timedelta(minutes=5),
    device_set_debounce=timedelta(seconds=1),
) -> List[Type[Device]]:
    """Initialize Devices available with the token."""
    client = _Client(
        token,
        session,
        conf_update_interval=conf_update_interval,
        device_set_debounce=device_set_debounce,
    )
    await client.update_confs()
    return [
        AtaDevice(conf, client, set_debounce=device_set_debounce)
        for conf in client.device_confs
        if conf.get("Device", {}).get("DeviceType", -1) == 0
    ] + [
        AtwDevice(conf, client, set_debounce=device_set_debounce)
        for conf in client.device_confs
        if conf.get("Device", {}).get("DeviceType", -1) == 1
    ]
