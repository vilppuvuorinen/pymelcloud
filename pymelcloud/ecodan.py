"""Ecodan air source heat pump (DeviceType=1) device definition."""
from typing import Any, Dict, List, Optional

from pymelcloud.device import Device, EFFECTIVE_FLAGS

OPERATION_MODE_OFF = "off"
OPERATION_MODE_WATER_HEATER = "water_heater"
OPERATION_MODE_HEAT = "heat"
OPERATION_MODE_COOL = "cool"
OPERATION_MODE_DEFROST = "defrost"
OPERATION_MODE_STANDBY = "standby"
OPERATION_MODE_LEGIONELLA = "legionella"
OPERATION_MODE_UNDEFINED = "undefined"

_OPERATION_MODE_LOOKUP = {
    0: OPERATION_MODE_OFF,
    1: OPERATION_MODE_WATER_HEATER,
    2: OPERATION_MODE_HEAT,
    3: OPERATION_MODE_COOL,
    4: OPERATION_MODE_DEFROST,
    5: OPERATION_MODE_STANDBY,
    6: OPERATION_MODE_LEGIONELLA,
}

def _operation_mode_from(mode: int) -> str:
    return _OPERATION_MODE_LOOKUP.get(mode, OPERATION_MODE_UNDEFINED)

def _operation_mode_to(mode: str) -> int:
    for k, value in _OPERATION_MODE_LOOKUP.items():
        if value == mode:
            return k
    raise ValueError(f"Invalid operation mode [{mode}]")

ZONE_OPERATION_MODE_HEAT = "heat"
ZONE_OPERATION_MODE_UNDEFINED = "undefined"

_ZONE_OPERATION_MODE_LOOKUP = {
    1: ZONE_OPERATION_MODE_HEAT,
}

def _zone_operation_mode_from(mode: int) -> str:
    return _ZONE_OPERATION_MODE_LOOKUP.get(mode, ZONE_OPERATION_MODE_UNDEFINED)

def _zone_operation_mode_to(mode: str) -> int:
    for k, value in _ZONE_OPERATION_MODE_LOOKUP.items():
        if value == mode:
            return k
    raise ValueError(f"Invalid zone_operation_mode [{mode}]")

class Zone:
    """Zone controlled by Ecodan device."""

    def __init__(self, device_state: dict, zone_index: int):
        """Initialize Zone."""
        self._device_state = device_state
        self.zone_index = zone_index

    @property
    def name(self) -> Optional[str]:
        """Return zone name if defined."""
        return self._device_state.get(f"Zone{self.zone_index}", None)

    @property
    def prohibit(self) -> bool:
        """Return prohibit flag of the zone."""
        return self._device_state.get(f"ProhibitZone{self.zone_index}")

    @property
    def operation_mode(self) -> str:
        """Return active operation mode."""
        return _zone_operation_mode_from(
            self._device_state.get(f"OperationModeZone{self.zone_index}")
        )

    @property
    def room_temperature(self) -> float:
        """Return room temperature."""
        return self._device_state.get(f"RoomTemperatureZone{self.zone_index}")

    @property
    def target_temperature(self) -> float:
        """Return target temperature."""
        return self._device_state.get(f"SetTemperatureZone{self.zone_index}")

    @property
    def target_cool_flow_temperature(self) -> float:
        """Return target cool flow temperature."""
        return self._device_state.get(f"SetCoolFlowTemperatureZone{self.zone_index}")

    @property
    def target_heat_flow_temperature(self) -> float:
        """Return target heat flow temperature."""
        return self._device_state.get(f"SetHeatFlowTemperatureZone{self.zone_index}")

class Ecodan(Device):
    """Ecodan device."""

    def apply_write(self, state: Dict[str, Any], key: str, value: Any):
        """Apply writes to state object."""
        flags = state.get(EFFECTIVE_FLAGS, 0)

        state[EFFECTIVE_FLAGS] = flags

    @property
    def tank_temperature(self) -> Optional[float]:
        """Return tank water temperature."""
        if self._state is None:
            return None
        return self._state.get("TankWaterTemperature")

    @property
    def target_tank_temperature(self) -> Optional[float]:
        """Return target tank water temperature."""
        if self._state is None:
            return None
        return self._state.get("SetTankWaterTemperature")

    @property
    def outdoor_temperature(self) -> Optional[float]:
        """Return outdoor temperature reported by the device."""
        if self._state is None:
            return None
        return self._state.get("OutdoorTemperature")

    @property
    def zones(self) -> Optional[List[Zone]]:
        """Return zones controlled by this device."""
        # TODO: Add logic for detecting number of supported zones.

        return [
            Zone(self._state, index)
            for index in [1, 2]
        ]

    @property
    def operation_mode(self) -> str:
        """Return active operation mode."""
        if self._state is None:
            return None
        return _operation_mode_from(
            self._state.get("OperationMode", -1)
        )
