"""Energy-Recovery-Ventilation (DeviceType=3) device definition."""
from typing import Any, Dict, List, Optional

from pymelcloud.device import EFFECTIVE_FLAGS, Device

PROPERTY_VENTILATION_MODE = "ventilation_mode"
PROPERTY_FAN_SPEED = "fan_speed"

FAN_SPEED_UNDEFINED = "undefined"
FAN_SPEED_STOPPED = "0"

VENTILATION_MODE_RECOVERY = "recovery"
VENTILATION_MODE_BYPASS = "bypass"
VENTILATION_MODE_AUTO = "auto"
VENTILATION_MODE_UNDEFINED = "undefined"

_VENTILATION_MODE_LOOKUP = {
    0: VENTILATION_MODE_RECOVERY,
    1: VENTILATION_MODE_BYPASS,
    2: VENTILATION_MODE_AUTO,
}


def _fan_speed_from(speed: int) -> str:
    if speed == -1:
        return FAN_SPEED_UNDEFINED
    if speed == 0:
        return FAN_SPEED_STOPPED
    return str(speed)


def _fan_speed_to(speed: str) -> int:
    if speed == FAN_SPEED_UNDEFINED:
        return -1
    if speed == FAN_SPEED_STOPPED:
        return 0
    return int(speed)


def _ventilation_mode_from(mode: int) -> str:
    return _VENTILATION_MODE_LOOKUP.get(mode, VENTILATION_MODE_UNDEFINED)


def _ventilation_mode_to(mode: str) -> int:
    for k, value in _VENTILATION_MODE_LOOKUP.items():
        if value == mode:
            return k
    raise ValueError(f"Invalid ventilation_mode [{mode}]")


class ErvDevice(Device):
    """Energy-Recovery-Ventilation device."""

    def apply_write(self, state: Dict[str, Any], key: str, value: Any):
        """Apply writes to state object.

        Used for property validation, do not modify device state.
        """
        flags = state.get(EFFECTIVE_FLAGS, 0)

        if key == PROPERTY_VENTILATION_MODE:
            state["VentilationMode"] = _ventilation_mode_to(value)
            flags = flags | 0x04
        elif key == PROPERTY_FAN_SPEED:
            state["SetFanSpeed"] = _fan_speed_to(value)
            flags = flags | 0x08
        else:
            raise ValueError(f"Cannot set {key}, invalid property")

        state[EFFECTIVE_FLAGS] = flags

    def _device(self) -> Dict[str, Any]:
        return self._device_conf.get("Device", {})

    @property
    def has_energy_consumed_meter(self) -> bool:
        """Return True if the device has an energy consumption meter."""
        if self._device_conf is None:
            return False
        return self._device().get("HasEnergyConsumedMeter", False)

    @property
    def total_energy_consumed(self) -> Optional[float]:
        """Return total consumed energy as kWh.

        The update interval is extremely slow and inconsistent. Empirical evidence
        suggests can vary between 1h 30min and 3h.
        """
        if self._device_conf is None:
            return None
        reading = self._device().get("CurrentEnergyConsumed", None)
        if reading is None:
            return None
        return reading / 1000.0

    @property
    def presets(self) -> List[Dict[Any, Any]]:
        """Return presets configuration (preset created using melcloud app)."""
        retval = []
        if self._device_conf is not None:
            presets_conf = self._device_conf.get("Presets", {})
            for p in presets_conf:
                retval.append(p)

        return retval

    @property
    def room_temperature(self) -> Optional[float]:
        """Return room temperature reported by the device."""
        if self._state is None:
            return None
        return self._state.get("RoomTemperature")

    @property
    def outside_temperature(self) -> Optional[float]:
        """Return outdoor temperature reported by the device."""
        if self._state is None:
            return None
        return self._state.get("OutdoorTemperature")

    @property
    def ventilation_mode(self) -> Optional[str]:
        """Return currently active ventilation mode."""
        if self._state is None:
            return None
        return _ventilation_mode_from(self._state.get("VentilationMode", -1))

    @property
    def actual_ventilation_mode(self) -> Optional[str]:
        """Return actual ventilation mode."""
        if self._state is None:
            return None
        return _ventilation_mode_from(self._device().get("ActualVentilationMode", -1))

    @property
    def fan_speed(self) -> Optional[str]:
        """Return currently active fan speed.

        The argument must be one of the fan speeds returned by fan_speeds.
        """
        if self._state is None:
            return None
        return _fan_speed_from(self._state.get("SetFanSpeed", -1))

    @property
    def actual_supply_fan_speed(self) -> Optional[str]:
        """Return actual supply fan speed.

        The argument must be one of the fan speeds returned by fan_speeds.
        """
        if self._state is None:
            return None
        return _fan_speed_from(self._device().get("ActualSupplyFanSpeed", -1))

    @property
    def actual_exhaust_fan_speed(self) -> Optional[str]:
        """Return actual exhaust fan speed.

        The argument must be one of the fan speeds returned by fan_speeds.
        """
        if self._state is None:
            return None
        return _fan_speed_from(self._device().get("ActualExhaustFanSpeed", -1))

    @property
    def core_maintenance_required(self) -> bool:
        """Return True if core maintenance required."""
        if self._device_conf is None:
            return False
        return self._device().get("CoreMaintenanceRequired", False)

    @property
    def filter_maintenance_required(self) -> bool:
        """Return True if filter maintenance required."""
        if self._device_conf is None:
            return False
        return self._device().get("FilterMaintenanceRequired", False)

    @property
    def night_purge_mode(self) -> bool:
        """Return True if NightPurgeMode."""
        if self._device_conf is None:
            return False
        return self._device().get("NightPurgeMode", False)

    @property
    def room_co2_level(self) -> Optional[float]:
        """Return co2 level if supported by the device."""
        if self._state is None:
            return None

        if not self._state.get("HasCO2Sensor", False):
            return None

        return self._device().get("RoomCO2Level", None)

    @property
    def fan_speeds(self) -> Optional[List[str]]:
        """Return available fan speeds.

        The supported fan speeds vary from device to device. The available modes are
        read from the Device capability attributes.

        For example, a 5 speed device with auto fan speed would produce the following
        list (formatted '"[pymelcloud]" -- "[device controls]"')

        - "auto" -- "auto"
        - "1" -- "silent"
        - "2" -- "1"
        - "3" -- "2"
        - "4" -- "3"
        - "5" -- "4"

        MELCloud is not aware of the device type making it infeasible to match the
        fan speed names with the device documentation.
        """
        if self._state is None:
            return None
        speeds = []

        num_fan_speeds = self._state.get("NumberOfFanSpeeds", 0)
        for num in range(1, num_fan_speeds + 1):
            speeds.append(_fan_speed_from(num))

        return speeds

    @property
    def ventilation_modes(self) -> List[str]:
        """Return available ventilation modes."""
        modes: List[str] = [VENTILATION_MODE_RECOVERY]

        device = self._device()

        if device.get("HasBypassVentilationMode", False):
            modes.append(VENTILATION_MODE_BYPASS)

        if device.get("HasAutoVentilationMode", False):
            modes.append(VENTILATION_MODE_AUTO)

        return modes
