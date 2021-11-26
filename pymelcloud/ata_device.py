"""Air-To-Air (DeviceType=0) device definition."""
from datetime import timedelta
from typing import Any, Dict, List, Optional

from pymelcloud.device import EFFECTIVE_FLAGS, Device
from pymelcloud.client import Client

PROPERTY_TARGET_TEMPERATURE = "target_temperature"
PROPERTY_OPERATION_MODE = "operation_mode"
PROPERTY_FAN_SPEED = "fan_speed"
PROPERTY_VANE_HORIZONTAL = "vane_horizontal"
PROPERTY_VANE_VERTICAL = "vane_vertical"

FAN_SPEED_AUTO = "auto"

OPERATION_MODE_HEAT = "heat"
OPERATION_MODE_DRY = "dry"
OPERATION_MODE_COOL = "cool"
OPERATION_MODE_FAN_ONLY = "fan_only"
OPERATION_MODE_HEAT_COOL = "heat_cool"
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

V_VANE_POSITION_AUTO = "auto"
V_VANE_POSITION_1 = "1_up"
V_VANE_POSITION_2 = "2"
V_VANE_POSITION_3 = "3"
V_VANE_POSITION_4 = "4"
V_VANE_POSITION_5 = "5_down"
V_VANE_POSITION_SWING = "swing"
V_VANE_POSITION_UNDEFINED = "undefined"


H_VANE_POSITION_AUTO = "auto"
H_VANE_POSITION_1 = "1_left"
H_VANE_POSITION_2 = "2"
H_VANE_POSITION_3 = "3"
H_VANE_POSITION_4 = "4"
H_VANE_POSITION_5 = "5_right"
H_VANE_POSITION_SPLIT = "split"
H_VANE_POSITION_SWING = "swing"
H_VANE_POSITION_UNDEFINED = "undefined"


def _fan_speed_from(speed: int) -> str:
    if speed == 0:
        return FAN_SPEED_AUTO
    return str(speed)


def _fan_speed_to(speed: str) -> int:
    if speed == FAN_SPEED_AUTO:
        return 0
    return int(speed)


def _operation_mode_from(mode: int) -> str:
    return _OPERATION_MODE_LOOKUP.get(mode, OPERATION_MODE_UNDEFINED)


def _operation_mode_to(mode: str) -> int:
    for k, value in _OPERATION_MODE_LOOKUP.items():
        if value == mode:
            return k
    raise ValueError(f"Invalid operation_mode [{mode}]")


_H_VANE_POSITION_LOOKUP = {
    0: H_VANE_POSITION_AUTO,
    1: H_VANE_POSITION_1,
    2: H_VANE_POSITION_2,
    3: H_VANE_POSITION_3,
    4: H_VANE_POSITION_4,
    5: H_VANE_POSITION_5,
    8: H_VANE_POSITION_SPLIT,
    12: H_VANE_POSITION_SWING,
}


def _horizontal_vane_from(position: int) -> str:
    return _H_VANE_POSITION_LOOKUP.get(position, H_VANE_POSITION_UNDEFINED)


def _horizontal_vane_to(position: str) -> int:
    for k, value in _H_VANE_POSITION_LOOKUP.items():
        if value == position:
            return k
    raise ValueError(f"Invalid horizontal vane position [{position}]")


_V_VANE_POSITION_LOOKUP = {
    0: V_VANE_POSITION_AUTO,
    1: V_VANE_POSITION_1,
    2: V_VANE_POSITION_2,
    3: V_VANE_POSITION_3,
    4: V_VANE_POSITION_4,
    5: V_VANE_POSITION_5,
    7: V_VANE_POSITION_SWING,
}


def _vertical_vane_from(position: int) -> str:
    return _V_VANE_POSITION_LOOKUP.get(position, V_VANE_POSITION_UNDEFINED)


def _vertical_vane_to(position: str) -> int:
    for k, value in _V_VANE_POSITION_LOOKUP.items():
        if value == position:
            return k
    raise ValueError(f"Invalid vertical vane position [{position}]")


class AtaDevice(Device):
    """Air-to-Air device."""

    def __init__(
        self,
        device_conf: Dict[str, Any],
        client: Client,
        set_debounce=timedelta(seconds=1),
    ):
        """Initialize an ATA device."""
        super().__init__(device_conf, client, set_debounce)
        self.last_energy_value = None

    def apply_write(self, state: Dict[str, Any], key: str, value: Any):
        """Apply writes to state object.

        Used for property validation, do not modify device state.
        """
        flags = state.get(EFFECTIVE_FLAGS, 0)

        if key == PROPERTY_TARGET_TEMPERATURE:
            state["SetTemperature"] = self.round_temperature(value)
            flags = flags | 0x04
        elif key == PROPERTY_OPERATION_MODE:
            state["OperationMode"] = _operation_mode_to(value)
            flags = flags | 0x02
        elif key == PROPERTY_FAN_SPEED:
            state["SetFanSpeed"] = _fan_speed_to(value)
            flags = flags | 0x08
        elif key == PROPERTY_VANE_HORIZONTAL:
            state["VaneHorizontal"] = _horizontal_vane_to(value)
            flags = flags | 0x100
        elif key == PROPERTY_VANE_VERTICAL:
            state["VaneVertical"] = _vertical_vane_to(value)
            flags = flags | 0x10
        else:
            raise ValueError(f"Cannot set {key}, invalid property")

        state[EFFECTIVE_FLAGS] = flags

    @property
    def has_energy_consumed_meter(self) -> bool:
        """Return True if the device has an energy consumption meter."""
        return self._device_conf.get("Device", {}).get("HasEnergyConsumedMeter", False)

    @property
    def total_energy_consumed(self) -> Optional[float]:
        """Return total consumed energy as kWh.

        The update interval is extremely slow and inconsistent. Empirical evidence
        suggests that it can vary between 1h 30min and 3h.
        """
        if self._device_conf is None:
            return None
        device = self._device_conf.get("Device", {})
        value = device.get("CurrentEnergyConsumed", None)
        if value is None:
            return None

        if value == 0.0:
            return self.last_energy_value

        self.last_energy_value = value / 1000.0
        return self.last_energy_value

    @property
    def room_temperature(self) -> Optional[float]:
        """Return room temperature reported by the device."""
        if self._state is None:
            return None
        return self._state.get("RoomTemperature")

    @property
    def target_temperature(self) -> Optional[float]:
        """Return target temperature set for the device."""
        if self._state is None:
            return None
        return self._state.get("SetTemperature")

    @property
    def target_temperature_step(self) -> float:
        """Return target temperature set precision."""
        return self.temperature_increment

    @property
    def target_temperature_min(self) -> Optional[float]:
        """Return maximum target temperature for the currently active operation mode."""
        if self._state is None:
            return None
        return self._device_conf.get("Device", {}).get(
            _OPERATION_MODE_MIN_TEMP_LOOKUP.get(self.operation_mode), 10
        )

    @property
    def target_temperature_max(self) -> Optional[float]:
        """Return maximum target temperature for the currently active operation mode."""
        if self._state is None:
            return None
        return self._device_conf.get("Device", {}).get(
            _OPERATION_MODE_MAX_TEMP_LOOKUP.get(self.operation_mode), 31
        )

    @property
    def operation_mode(self) -> str:
        """Return currently active operation mode."""
        if self._state is None:
            return OPERATION_MODE_UNDEFINED
        return _operation_mode_from(self._state.get("OperationMode", -1))

    @property
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
    def fan_speed(self) -> Optional[str]:
        """Return currently active fan speed.

        The argument must be on of the fan speeds returned by fan_speeds.
        """
        if self._state is None:
            return None
        return _fan_speed_from(self._state.get("SetFanSpeed"))

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
        if self._device_conf.get("Device", {}).get("HasAutomaticFanSpeed", False):
            speeds.append(FAN_SPEED_AUTO)

        num_fan_speeds = self._state.get("NumberOfFanSpeeds", 0)
        for num in range(1, num_fan_speeds + 1):
            speeds.append(_fan_speed_from(num))

        return speeds

    @property
    def vane_horizontal(self) -> Optional[str]:
        """Return horizontal vane position."""
        if self._state is None:
            return None
        return _horizontal_vane_from(self._state.get("VaneHorizontal"))

    @property
    def vane_horizontal_positions(self) -> Optional[List[str]]:
        """Return available horizontal vane positions."""
        if self._device_conf.get("HideVaneControls", False):
            return []
        device = self._device_conf.get("Device", {})
        if not device.get("ModelSupportsVaneHorizontal", False):
            return []

        positions = [
            H_VANE_POSITION_AUTO,  # ModelSupportsAuto could affect this.
            H_VANE_POSITION_1,
            H_VANE_POSITION_2,
            H_VANE_POSITION_3,
            H_VANE_POSITION_4,
            H_VANE_POSITION_5,
            H_VANE_POSITION_SPLIT,
        ]
        if device.get("SwingFunction", False):
            positions.append(H_VANE_POSITION_SWING)

        return positions

    @property
    def vane_vertical(self) -> Optional[str]:
        """Return vertical vane position."""
        if self._state is None:
            return None
        return _vertical_vane_from(self._state.get("VaneVertical"))

    @property
    def vane_vertical_positions(self) -> Optional[List[str]]:
        """Return available vertical vane positions."""
        if self._device_conf.get("HideVaneControls", False):
            return []
        device = self._device_conf.get("Device", {})
        if not device.get("ModelSupportsVaneVertical", False):
            return []

        positions = [
            V_VANE_POSITION_AUTO,  # ModelSupportsAuto could affect this.
            V_VANE_POSITION_1,
            V_VANE_POSITION_2,
            V_VANE_POSITION_3,
            V_VANE_POSITION_4,
            V_VANE_POSITION_5,
        ]
        if device.get("SwingFunction", False):
            positions.append(V_VANE_POSITION_SWING)

        return positions
