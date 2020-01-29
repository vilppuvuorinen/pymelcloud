"""Air-To-Water (DeviceType=1) device definition."""
from typing import Any, Dict, List, Optional

from pymelcloud.device import Device, EFFECTIVE_FLAGS

PROPERTY_TARGET_TANK_TEMPERATURE = "target_tank_temperature"
PROPERTY_OPERATION_MODE = "operation_mode"
PROPERTY_ZONE_1_TARGET_TEMPERATURE = "zone_1_target_temperature"
PROPERTY_ZONE_2_TARGET_TEMPERATURE = "zone_2_target_temperature"

OPERATION_MODE_AUTO = "auto"
OPERATION_MODE_FORCE_HOT_WATER = "force_hot_water"

STATE_OFF = "off"
STATE_HEAT = "heat"
STATE_IDLE = "idle"
STATE_COOL = "cool"
STATE_DEFROST = "defrost"
STATE_STANDBY = "standby"
STATE_LEGIONELLA = "legionella"
STATE_UNKNOWN = "unknown"

_STATE_LOOKUP = {
    0: STATE_OFF,
    1: STATE_HEAT,
    2: STATE_IDLE,
    3: STATE_COOL,
    4: STATE_DEFROST,
    5: STATE_STANDBY,
    6: STATE_LEGIONELLA,
}


ZONE_PROPERTY_TARGET_TEMPERATURE = "target_temperature"

ZONE_STATE_HEAT = "heat"
ZONE_STATE_IDLE = "idle"
ZONE_STATE_COOL = "cool"
ZONE_STATE_UNKNOWN = "unknown"

_ZONE_STATE_LOOKUP = {
    1: ZONE_STATE_HEAT,
    2: ZONE_STATE_IDLE,
    3: ZONE_STATE_COOL,  # I'm just guessing here.
}


class Zone:
    """Zone controlled by Air-to-Water device."""

    def __init__(self, device, device_state: dict, zone_index: int):
        """Initialize Zone."""
        self._device = device
        self._device_state = device_state
        self.zone_index = zone_index

    @property
    def name(self) -> Optional[str]:
        """Return zone name if defined."""
        return self._device_state.get(
            f"Zone{self.zone_index}", f"Zone {self.zone_index}"
        )

    @property
    def prohibit(self) -> bool:
        """Return prohibit flag of the zone."""
        return self._device_state.get(f"ProhibitZone{self.zone_index}")

    @property
    def state(self) -> str:
        """Return the current state."""
        return _ZONE_STATE_LOOKUP.get(
            self._device_state.get(f"OperationModeZone{self.zone_index}"),
            ZONE_STATE_UNKNOWN,
        )

    @property
    def room_temperature(self) -> float:
        """Return room temperature."""
        return self._device_state.get(f"RoomTemperatureZone{self.zone_index}")

    @property
    def target_temperature(self) -> float:
        """Return target temperature."""
        return self._device_state.get(f"SetTemperatureZone{self.zone_index}")

    def set_target_temperature(self, target_temperature):
        """Set target temperature for this zone."""
        return self._device.set(
            {f"zone_{self.zone_index}_target_temperature": target_temperature}
        )


class AtwDevice(Device):
    """Air-to-Water device."""

    def apply_write(self, state: Dict[str, Any], key: str, value: Any):
        """Apply writes to state object."""
        flags = state.get(EFFECTIVE_FLAGS, 0)

        if key == PROPERTY_TARGET_TANK_TEMPERATURE:
            state["SetTankWaterTemperature"] = value
            flags = flags | 281474976710688
        elif key == PROPERTY_OPERATION_MODE:
            state["ForcedHotWaterMode"] = value == OPERATION_MODE_FORCE_HOT_WATER
            flags = flags | 65536
        elif key == PROPERTY_ZONE_1_TARGET_TEMPERATURE:
            state["SetTemperatureZone1"] = value
            flags = flags | 8589934720
        elif key == PROPERTY_ZONE_2_TARGET_TEMPERATURE:
            state["SetTemperatureZone2"] = value
            flags = flags | 34359738880
        else:
            raise ValueError(f"Cannot set {key}, invalid property")

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
    def target_tank_temperature_min(self) -> Optional[float]:
        """Return minimum target tank water temperature."""
        device = self._device_conf.get("Device", {})
        return device.get("MinSetTemperature")

    @property
    def target_tank_temperature_max(self) -> Optional[float]:
        """Return maximum target tank water temperature."""
        device = self._device_conf.get("Device", {})
        return device.get("MaxSetTemperature")

    @property
    def outside_temperature(self) -> Optional[float]:
        """Return outdoor temperature reported by the device."""
        if self._state is None:
            return None
        return self._state.get("OutdoorTemperature")

    @property
    def zones(self) -> Optional[List[Zone]]:
        """
        Return zones controlled by this device.
        
        Zones without a thermostat are not returned.
        """
        _zones = []

        device = self._device_conf.get("Device", {})
        if device.get("HasThermostatZone1", False):
            _zones.append(Zone(self, self._state, 1))

        if device.get("HasZone2") and device.get("HasThermostatZone2", False):
            _zones.append(Zone(self, self._state, 2))

        return _zones

    @property
    def state(self) -> Optional[str]:
        """Return current state."""
        if self._state is None:
            return None
        return _STATE_LOOKUP.get(self._state.get("OperationMode", -1), STATE_UNKNOWN)

    @property
    def operation_mode(self) -> Optional[str]:
        """Return active operation mode."""
        if self._state is None:
            return None
        if self._state.get("ForcedHotWaterMode", False):
            return OPERATION_MODE_FORCE_HOT_WATER
        return OPERATION_MODE_AUTO

    @property
    def operation_modes(self) -> List[str]:
        """Return available operation modes."""
        return [OPERATION_MODE_AUTO, OPERATION_MODE_FORCE_HOT_WATER]
