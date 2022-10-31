"""Base MELCloud device."""
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from pymelcloud.client import Client
from pymelcloud.const import (
    DEVICE_TYPE_LOOKUP,
    DEVICE_TYPE_UNKNOWN,
    UNIT_TEMP_CELSIUS,
    UNIT_TEMP_FAHRENHEIT,
    ACCESS_LEVEL,
)

PROPERTY_POWER = "power"

EFFECTIVE_FLAGS = "EffectiveFlags"
HAS_PENDING_COMMAND = "HasPendingCommand"


class Device(ABC):
    """MELCloud base device representation."""

    def __init__(
        self,
        device_conf: Dict[str, Any],
        client: Client,
        set_debounce=timedelta(seconds=1),
    ):
        """Initialize a device."""
        self.device_id = device_conf.get("DeviceID")
        self.building_id = device_conf.get("BuildingID")
        self.mac = device_conf.get("MacAddress")
        self.serial = device_conf.get("SerialNumber")
        self.access_level = device_conf.get("AccessLevel")

        self._use_fahrenheit = False
        if client.account is not None:
            self._use_fahrenheit = client.account.get("UseFahrenheit", False)

        self._device_conf = device_conf
        self._state = None
        self._device_units = None
        self._energy_report = None
        self._client = client

        self._set_debounce = set_debounce
        self._set_event = asyncio.Event()
        self._write_task: Optional[asyncio.Future[None]] = None
        self._pending_writes: Dict[str, Any] = {}

    def get_device_prop(self, name: str) -> Optional[Any]:
        """Access device properties while shortcutting the nested device access."""
        device = self._device_conf.get("Device", {})
        return device.get(name)

    def get_state_prop(self, name: str) -> Optional[Any]:
        """Access state prop without None check."""
        if self._state is None:
            return None
        return self._state.get(name)

    def round_temperature(self, temperature: float) -> float:
        """Round a temperature to the nearest temperature increment."""
        return float(
            Decimal(str(temperature / self.temperature_increment))
            .quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        ) * self.temperature_increment

    @abstractmethod
    def apply_write(self, state: Dict[str, Any], key: str, value: Any):
        """Apply writes to state object.

        Used for property validation, do not modify device state.
        """
        pass

    async def update(self):
        """Fetch state of the device from MELCloud.

        List of device_confs is also updated.

        Please, rate limit calls to this method. Polling every 60 seconds should be
        enough to catch all events at the rate they are coming in to MELCloud with the
        exception of changes performed through MELCloud directly.
        """
        await self._client.update_confs()
        self._device_conf = next(
            c
            for c in self._client.device_confs
            if c.get("DeviceID") == self.device_id
            and c.get("BuildingID") == self.building_id
        )
        self._state = await self._client.fetch_device_state(self)
        self._energy_report = await self._client.fetch_energy_report(self)

        if self._device_units is None and self.access_level != ACCESS_LEVEL.get(
            "GUEST"
        ):
            self._device_units = await self._client.fetch_device_units(self)

    async def set(self, properties: Dict[str, Any]):
        """Schedule property write to MELCloud."""
        if self._write_task is not None:
            self._write_task.cancel()

        for k, value in properties.items():
            if k == PROPERTY_POWER:
                continue
            self.apply_write({}, k, value)

        self._pending_writes.update(properties)

        self._write_task = asyncio.ensure_future(self._write())
        await self._set_event.wait()

    async def _write(self):
        await asyncio.sleep(self._set_debounce.total_seconds())
        new_state = self._state.copy()

        for k, value in self._pending_writes.items():
            if k == PROPERTY_POWER:
                new_state["Power"] = value
                new_state[EFFECTIVE_FLAGS] = new_state.get(EFFECTIVE_FLAGS, 0) | 0x01
            else:
                self.apply_write(new_state, k, value)

        if new_state[EFFECTIVE_FLAGS] != 0:
            new_state.update({HAS_PENDING_COMMAND: True})

        self._pending_writes = {}
        self._state = await self._client.set_device_state(new_state)
        self._set_event.set()
        self._set_event.clear()

    @property
    def name(self) -> str:
        """Return device name."""
        return self._device_conf["DeviceName"]

    @property
    def device_type(self) -> str:
        """Return type of the device."""
        return DEVICE_TYPE_LOOKUP.get(
            self._device_conf.get("Device", {}).get("DeviceType", -1),
            DEVICE_TYPE_UNKNOWN,
        )

    @property
    def units(self) -> Optional[List[dict]]:
        """Return device model info."""
        if self._device_units is None:
            return None

        infos: List[dict] = []
        for unit in self._device_units:
            infos.append(
                {
                    "model_number": unit.get("ModelNumber"),
                    "model": unit.get("Model"),
                    "serial_number": unit.get("SerialNumber"),
                }
            )
        return infos

    @property
    def temp_unit(self) -> str:
        """Return temperature unit used by the device."""
        if self._use_fahrenheit:
            return UNIT_TEMP_FAHRENHEIT
        return UNIT_TEMP_CELSIUS

    @property
    def temperature_increment(self) -> float:
        """Return temperature increment."""
        return self._device_conf.get("Device", {}).get("TemperatureIncrement", 0.5)

    @property
    def last_seen(self) -> Optional[datetime]:
        """Return timestamp of the last communication from device to MELCloud.

        The timestamp is in UTC.
        """
        if self._state is None:
            return None
        return datetime.strptime(
            self._state.get("LastCommunication"), "%Y-%m-%dT%H:%M:%S.%f"
        ).replace(tzinfo=timezone.utc)

    @property
    def power(self) -> Optional[bool]:
        """Return power on / standby state of the device."""
        if self._state is None:
            return None
        return self._state.get("Power")

    @property
    def daily_energy_consumed(self) -> Optional[float]:
        """Return daily energy consumption for the current day in kWh.

        The value resets at midnight MELCloud time. The logic here is a bit iffy and
        fragmented between Device and Client. Here's how it goes:
          - Client requests a 5 day report. Today, 2 days from the past and 2 days from
            the past.
          - MELCloud, with its clock potentially set to a different timezone than the
            client, returns a report containing data from a couple of days from the
            past and from the current day in MELCloud time.
          - Device sums up the date from the last day bucket in the report.

        TLDR: Request some days from the past and some days from the future -> receive
        the latest day bucket.
        """
        if self._energy_report is None:
            return None

        consumption = 0

        for mode in ['Heating', 'Cooling', 'Auto', 'Dry', 'Fan', 'Other']:
            previous_reports = self._energy_report.get(mode, [0.0])
            if previous_reports:
                last_report = previous_reports[-1]
            else:
                last_report = 0.0
            consumption += last_report

        return consumption

    @property
    def wifi_signal(self) -> Optional[int]:
        """Return wifi signal in dBm (negative value)."""
        if self._device_conf is None:
            return None
        return self._device_conf.get("Device", {}).get("WifiSignalStrength", None)

    @property
    def has_error(self) -> bool:
        """Return True if the device has error state."""
        if self._state is None:
            return False
        return self._state.get("HasError", False)

    @property
    def error_code(self) -> Optional[str]:
        """Return error_code.
        This is a property that probably should be checked if "has_error" = true
        Till now I have a fixed code = 8000 and never have error on the units
        """
        if self._state is None:
            return None
        return self._state.get("ErrorCode", None)
