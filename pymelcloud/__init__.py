"""MEL module"""
from aiohttp import ClientSession
import asyncio
import datetime as dt
from typing import Dict, List, Optional

BASE_URL = "https://app.melcloud.com/Mitsubishi.Wifi.Client"


def _headers(token: str) -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "X-MitsContextKey": token,
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": "policyaccepted=true",
    }


FAN_SPEED_AUTO = "auto"
FAN_SPEED_SLUG = "speed-"


def _fanSpeedFrom(speed: int) -> str:
    if speed == 0:
        return FAN_SPEED_AUTO

    return f"{FAN_SPEED_SLUG}{speed}"


def _fanSpeedTo(speed: str) -> int:
    if speed == FAN_SPEED_AUTO:
        return 0

    return int(speed[len(FAN_SPEED_SLUG) :])


OPERATION_MODE_HEAT = "heat"
OPERATION_MODE_DRY = "dry"
OPERATION_MODE_COOL = "cool"
OPERATION_MODE_FAN_ONLY = "fan-only"
OPERATION_MODE_HEAT_COOL = "heat-cool"
OPERATION_MODE_UNDEFINED = "undefined"

_OPERATION_MODE_LOOKUP = {
    1: OPERATION_MODE_HEAT,
    2: OPERATION_MODE_DRY,
    3: OPERATION_MODE_COOL,
    7: OPERATION_MODE_FAN_ONLY,
    8: OPERATION_MODE_HEAT_COOL,
}

_OPERATION_MODE_MIN_TEMP_LOOKUP = {
    OPERATION_MODE_HEAT: "MinTempHeat",
    OPERATION_MODE_DRY: "MinTempCoolDry",
    OPERATION_MODE_COOL: "MinTempCoolDry",
    OPERATION_MODE_FAN_ONLY: "MinTempHeat",  # Fake it just in case.
    OPERATION_MODE_HEAT_COOL: "MinTempAutomatic",
    OPERATION_MODE_UNDEFINED: "MinTempHeat",
}

_OPERATION_MODE_MAX_TEMP_LOOKUP = {
    OPERATION_MODE_HEAT: "MaxTempHeat",
    OPERATION_MODE_DRY: "MaxTempCoolDry",
    OPERATION_MODE_COOL: "MaxTempCoolDry",
    OPERATION_MODE_FAN_ONLY: "MaxTempHeat",  # Fake it just in case.
    OPERATION_MODE_HEAT_COOL: "MaxTempAutomatic",
    OPERATION_MODE_UNDEFINED: "MaxTempHeat",
}


def _operationModeFrom(mode: int) -> str:
    return _OPERATION_MODE_LOOKUP.get(mode, OPERATION_MODE_UNDEFINED)


def _operationModeTo(mode: str) -> int:
    for k, v in _OPERATION_MODE_LOOKUP.items():
        if v == mode:
            return k
    raise ValueError(f"Invalid operation_mode [{mode}]")


_SET_PROPERTY_LOOKUP = {
    "power": "Power",
    "target_temperature": "SetTemperature",
    "operation_mode": "OperationMode",
    "fan_speed": "SetFanSpeed",
}

UNIT_TEMP_CELSIUS = "celsius"
UNIT_TEMP_FAHRENHEIT = "fahrenheit"


class Client:
    """MELCloud client"""

    def __init__(
        self,
        token: str,
        session: Optional[ClientSession] = None,
        conf_update_interval: Optional[dt.timedelta] = None,
        device_set_debounce: Optional[dt.timedelta] = None,
    ):
        """Initialize MELCloud client"""
        self._token = token
        if session:
            self._session = session
            self._managed_session = False
        else:
            self._session = ClientSession()
            self._managed_session = True
        self._conf_update_interval = conf_update_interval
        if self._conf_update_interval is None:
            self._conf_update_interval = dt.timedelta(milliseconds=500)
        self._device_set_debounce = device_set_debounce

        self._last_update = None
        self._device_confs = []
        self._account = None

    async def __del__(self):
        if self._managed_session and not self._session.closed:
            await self._session.close()

    @staticmethod
    async def login(email: str, password: str, session: Optional[ClientSession] = None):
        """
		Login using email and password. An additional language argument can
		be provided.
		"""

        async def do_login(_session: ClientSession):
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

        if session:
            response = await do_login(session)
        else:
            async with ClientSession() as _session:
                response = await do_login(_session)

        return Client(response.get("LoginData").get("ContextKey"), session)

    async def get_devices(self) -> List[any]:
        """Build Device instances of all available devices."""
        await self.update_confs()
        return [
            Device(conf, self, set_debounce=self._device_set_debounce)
            for conf in self._device_confs
        ]

    async def _fetch_user_details(self):
        """Fetch user details."""
        async with self._session.get(
            f"{BASE_URL}/User/GetUserDetails",
            headers=_headers(self._token),
            raise_for_status=True,
        ) as resp:
            self._account = await resp.json()

    async def _fetch_device_confs(self):
        """Fetch all configured devices"""
        url = f"{BASE_URL}/User/ListDevices"
        async with self._session.get(
            url, headers=_headers(self._token), raise_for_status=True
        ) as resp:
            entries = await resp.json()
            new_devices = []
            for entry in entries:
                new_devices = new_devices + entry["Structure"]["Devices"]

                # This loopyboi is most likely unnecessary. I'll just leave it here
                # for future generations to marvel at.
                for floor in entry["Structure"]["Floors"]:
                    for device in floor["Devices"]:
                        new_devices.append(device)

                    for areas in floor["Areas"]:
                        for device in areas["Devices"]:
                            new_devices.append(device)

            visited = set()
            self._device_confs = [
                d
                for d in new_devices
                if d["DeviceID"] not in visited and not visited.add(d["DeviceID"])
            ]

    async def update_confs(self):
        """
		Update device_confs and account. Calls are rate limited to allow Device
		instances to freely poll their own state while refreshing the device_confs
		list and account.
		"""
        now = dt.datetime.now()
        if (
            self._last_update is not None
            and now - self._last_update < self._conf_update_interval
        ):
            return None

        self._last_update = now
        await self._fetch_user_details()
        await self._fetch_device_confs()

    async def _get_device_state(self, device) -> Optional[dict]:
        async with self._session.get(
            f"{BASE_URL}/Device/Get?id={device.device_id}&buildingID={device.building_id}",
            headers=_headers(self._token),
            raise_for_status=True,
        ) as resp:
            return await resp.json()

    async def _set_device_state(self, device):
        async with self._session.post(
            f"{BASE_URL}/Device/SetAta",
            headers=_headers(self._token),
            json=device,
            raise_for_status=True,
        ) as resp:
            return await resp.json()


class Device:
    """MELCloud Device representation."""

    def __init__(
        self,
        device_conf: dict,
        client: Client,
        set_debounce: Optional[dt.timedelta] = None,
    ):
        self.device_id = device_conf.get("DeviceID")
        self.building_id = device_conf.get("BuildingID")
        self.mac = device_conf.get("MacAddress")
        self.serial = device_conf.get("SerialNumber")

        self._use_fahrenheit = client._account.get("UseFahrenheit")

        self._device_conf = device_conf
        self._state = None
        self._client = client

        self._set_debounce = set_debounce
        if self._set_debounce is None:
            self._set_debounce = dt.timedelta(milliseconds=500)
        self._write_task = None
        self._pending_writes = {}

    async def update(self):
        """
		Fetch state of the device from MELCloud. List of devicec_confs is also
		updated.
		"""
        await self._client.update_confs()
        self._device_conf = next(
            c
            for c in self._client._device_confs
            if c.get("DeviceID") == self.device_id
            and c.get("BuildingID") == self.building_id
        )
        self._state = await self._client._get_device_state(self)

    def set_debounce(self, delta: dt.timedelta):
        self._write_debounce = delta

    def disable_debounce(self):
        self._write_debounce = None

    def set(self, properties: Dict[str, any]):
        """Schedule property write to MELCloud"""
        if self._write_task is not None:
            self._write_task.cancel()

        for k, v in properties.items():
            assert k in _SET_PROPERTY_LOOKUP.keys()
            prop = _SET_PROPERTY_LOOKUP.get(k)

            if k == "fan_speed":
                self._pending_writes.update({prop: _fanSpeedTo(v)})
                continue

            if k == "operation_mode":
                self._pending_writes.update({prop: _operationModeTo(v)})
                continue

            self._pending_writes.update({prop: v})

        self._write_task = asyncio.ensure_future(self._write())

    async def _write(self):
        await asyncio.sleep(self._set_debounce.total_seconds())
        new_state = self._state.copy()
        new_state.update(self._pending_writes)

        flags = 0
        if _SET_PROPERTY_LOOKUP.get("power") in self._pending_writes.keys():
            flags = flags | 0x01
        if _SET_PROPERTY_LOOKUP.get("operation_mode") in self._pending_writes.keys():
            flags = flags | 0x02
        if _SET_PROPERTY_LOOKUP.get("temperature") in self._pending_writes.keys():
            flags = flags | 0x04
        if _SET_PROPERTY_LOOKUP.get("fan_speed") in self._pending_writes.keys():
            flags = flags | 0x08

        # TODO: vane vertical 0x010
        # TODO: vane horizontal 0x100
        if flags != 0:
            new_state.update({"EffectiveFlags": flags, "HasPendingCommand": True})

        self._state = await self._client._set_device_state(new_state)

    @property
    def name(self) -> str:
        """Return device name."""
        return self._device_conf.get("DeviceName")

    @property
    def temp_unit(self) -> str:
        """Return temperature unit used by the device."""
        if self._use_fahrenheit:
            return UNIT_TEMP_FAHRENHEIT
        return UNIT_TEMP_CELSIUS

    @property
    def last_seen(self) -> dt.datetime:
        """
		Return timestamp of the last communication between MELCloud and
		the device in UTC.
		"""
        return dt.datetime.strptime(
            self._state.get("LastCommunication"), "%Y-%m-%dT%H:%M:%S.%f"
        )

    @property
    def power(self) -> bool:
        """Return power on / standby state of the device."""
        return self._state.get(_SET_PROPERTY_LOOKUP.get("power"))

    @property
    def temperature(self) -> float:
        """Return room temperature reported by the device."""
        return self._state.get("RoomTemperature")

    @property
    def target_temperature(self) -> float:
        """Return target temperature set for the device."""
        return self._state.get(_SET_PROPERTY_LOOKUP.get("target_temperature"))

    @property
    def target_temperature_step(self) -> float:
        """Return target temperature set precision."""
        return self._device_conf.get("Device", {}).get("TemperatureIncrement", 0.5)

    @property
    def target_temperature_min(self) -> float:
        """
		Return maximum target temperature for the currently active operation mode.
		"""
        return self._device_conf.get("Device", {}).get(
            _OPERATION_MODE_MIN_TEMP_LOOKUP.get(self.operation_mode), 10
        )

    @property
    def target_temperature_max(self) -> float:
        """
		Return maximum target temperature for the currently active operation mode.
		"""
        return self._device_conf.get("Device", {}).get(
            _OPERATION_MODE_MAX_TEMP_LOOKUP.get(self.operation_mode), 31
        )

    @property
    def operation_mode(self) -> str:
        """Return currently active operation mode."""
        return _operationModeFrom(
            self._state.get(_SET_PROPERTY_LOOKUP.get("operation_mode"), -1)
        )

    def operation_modes(self) -> List[str]:
        """Return available operation modes."""
        modes: List[str] = []

        conf_dev = self._device_conf.get("Device", {})
        if conf_dev.get("CanHeat", False):
            modes.append(OPERATION_MODE_HEAT)

        if conf_dev.get("CanDry", False):
            modes.append(OPERATION_MODE_DRY)

        if conf_dev.get("CanCool", False):
            modes.append(OPERATION_MODE_COOL)

        modes.append(OPERATION_MODE_FAN_ONLY)

        if conf_dev.get("ModelSupportsAuto", False):
            modes.append(OPERATION_MODE_HEAT_COOL)

        return modes

    @property
    def fan_speed(self) -> str:
        """Return currently active fan speed."""
        return _fanSpeedFrom(self._state.get(_SET_PROPERTY_LOOKUP.get("fan_speed")))

    def fan_speeds(self) -> List[str]:
        """Return available fan speeds."""
        speeds = []
        if self._device_conf.get("Device", {}).get("HasAutomaticFanSpeed", False):
            speeds.append(FAN_SPEED_AUTO)

        num_fan_speeds = self._state.get("NumberOfFanSpeeds", 0)
        for num in range(1, num_fan_speeds + 1):
            speeds.append(_fanSpeedFrom(num))

        return speeds
