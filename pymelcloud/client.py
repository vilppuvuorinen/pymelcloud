"""MEL API access."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession

BASE_URL = "https://app.melcloud.com/Mitsubishi.Wifi.Client"


def _headers(token: str) -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:73.0) "
        "Gecko/20100101 Firefox/73.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "X-MitsContextKey": token,
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": "policyaccepted=true",
    }


async def _do_login(_session: ClientSession, email: str, password: str):
    body = {
        "Email": email,
        "Password": password,
        "Language": 0,
        "AppVersion": "1.19.1.1",
        "Persist": True,
        "CaptchaResponse": None,
    }

    async with _session.post(
        f"{BASE_URL}/Login/ClientLogin", json=body, raise_for_status=True
    ) as resp:
        return await resp.json()


async def login(
    email: str,
    password: str,
    session: Optional[ClientSession] = None,
    *,
    conf_update_interval: Optional[timedelta] = None,
    device_set_debounce: Optional[timedelta] = None,
):
    """Login using email and password."""
    if session:
        response = await _do_login(session, email, password)
    else:
        async with ClientSession() as _session:
            response = await _do_login(_session, email, password)

    return Client(
        response.get("LoginData").get("ContextKey"),
        session,
        conf_update_interval=conf_update_interval,
        device_set_debounce=device_set_debounce,
    )


class Client:
    """MELCloud client.

    Please do not use this class directly. It is better to use the get_devices
    method exposed by the __init__.py.
    """

    def __init__(
        self,
        token: str,
        session: Optional[ClientSession] = None,
        *,
        conf_update_interval=timedelta(minutes=5),
        device_set_debounce=timedelta(seconds=1),
    ):
        """Initialize MELCloud client."""
        self._token = token
        if session:
            self._session = session
            self._managed_session = False
        else:
            self._session = ClientSession()
            self._managed_session = True
        self._conf_update_interval = conf_update_interval
        self._device_set_debounce = device_set_debounce

        self._last_conf_update = None
        self._device_confs: List[Dict[str, Any]] = []
        self._account: Optional[Dict[str, Any]] = None

    @property
    def token(self) -> str:
        """Return currently used token."""
        return self._token

    @property
    def device_confs(self) -> List[Dict[Any, Any]]:
        """Return device configurations."""
        return self._device_confs

    @property
    def account(self) -> Optional[Dict[Any, Any]]:
        """Return account."""
        return self._account

    async def _fetch_user_details(self):
        """Fetch user details."""
        async with self._session.get(
            f"{BASE_URL}/User/GetUserDetails",
            headers=_headers(self._token),
            raise_for_status=True,
        ) as resp:
            self._account = await resp.json()

    async def _fetch_device_confs(self):
        """Fetch all configured devices."""
        url = f"{BASE_URL}/User/ListDevices"
        async with self._session.get(
            url, headers=_headers(self._token), raise_for_status=True
        ) as resp:
            entries = await resp.json()
            new_devices = []
            for entry in entries:
                new_devices = new_devices + entry["Structure"]["Devices"]

                for area in entry["Structure"]["Areas"]:
                    new_devices = new_devices + area["Devices"]

                for floor in entry["Structure"]["Floors"]:
                    new_devices = new_devices + floor["Devices"]

                    for area in floor["Areas"]:
                        new_devices = new_devices + area["Devices"]

            visited = set()
            self._device_confs = [
                d
                for d in new_devices
                if d["DeviceID"] not in visited and not visited.add(d["DeviceID"])
            ]

    async def update_confs(self):
        """Update device_confs and account.

        Calls are rate limited to allow Device instances to freely poll their own
        state while refreshing the device_confs list and account.
        """
        now = datetime.now()
        if (
            self._last_conf_update is not None
            and now - self._last_conf_update < self._conf_update_interval
        ):
            return None

        self._last_conf_update = now
        await self._fetch_user_details()
        await self._fetch_device_confs()

    async def fetch_device_units(self, device) -> Optional[Dict[Any, Any]]:
        """Fetch unit information for a device.

        User provided info such as indoor/outdoor unit model names and
        serial numbers.
        """
        async with self._session.post(
            f"{BASE_URL}/Device/ListDeviceUnits",
            headers=_headers(self._token),
            json={"deviceId": device.device_id},
            raise_for_status=True,
        ) as resp:
            return await resp.json()

    async def fetch_device_state(self, device) -> Optional[Dict[Any, Any]]:
        """Fetch state information of a device.

        This method should not be called more than once a minute. Rate
        limiting is left to the caller.
        """
        device_id = device.device_id
        building_id = device.building_id
        async with self._session.get(
            f"{BASE_URL}/Device/Get?id={device_id}&buildingID={building_id}",
            headers=_headers(self._token),
            raise_for_status=True,
        ) as resp:
            return await resp.json()

    async def set_device_state(self, device):
        """Update device state.

        This method is as dumb as it gets. Device is responsible for updating
        the state and managing EffectiveFlags.
        """
        device_type = device.get("DeviceType")
        if device_type == 0:
            setter = "SetAta"
        elif device_type == 1:
            setter = "SetAtw"
        else:
            raise ValueError(f"Unsupported device type [{device_type}]")

        async with self._session.post(
            f"{BASE_URL}/Device/{setter}",
            headers=_headers(self._token),
            json=device,
            raise_for_status=True,
        ) as resp:
            return await resp.json()
