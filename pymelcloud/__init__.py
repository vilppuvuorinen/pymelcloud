"""MELCloud client library."""
from datetime import timedelta
from typing import Dict, List, Optional

from aiohttp import ClientSession

from pymelcloud.ata_device import AtaDevice
from pymelcloud.atw_device import AtwDevice
from pymelcloud.client import Client as _Client
from pymelcloud.client import login as _login
from pymelcloud.const import DEVICE_TYPE_ATA, DEVICE_TYPE_ATW
from pymelcloud.device import Device


async def login(
    email: str, password: str, session: Optional[ClientSession] = None,
) -> str:
    """Log in to MELCloud with given credentials.

    Returns access token.
    """
    _client = await _login(email, password, session,)
    return _client.token


async def get_devices(
    token: str,
    session: Optional[ClientSession] = None,
    *,
    conf_update_interval=timedelta(minutes=5),
    device_set_debounce=timedelta(seconds=1),
) -> Dict[str, List[Device]]:
    """Initialize Devices available with the token.

    The devices share a the same Client instance and pool config fetches. The devices
    should be fetched only once during application life cycle to leverage the request
    pooling and rate limits.

    Keyword arguments:
        conf_update_interval -- rate limit for fetching device confs. (default = 5 min)
        device_set_debounce -- debounce time for writing device state. (default = 1 s)
    """
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
