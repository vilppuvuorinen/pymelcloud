"""Air-To-Water (DeviceType=1) device definition."""
from typing import Any, Callable, Dict, List, Optional

from pymelcloud.device import EFFECTIVE_FLAGS, Device

PROPERTY_TARGET_TANK_TEMPERATURE = "target_tank_temperature"
PROPERTY_OPERATION_MODE = "operation_mode"
PROPERTY_ZONE_1_TARGET_TEMPERATURE = "zone_1_target_temperature"
PROPERTY_ZONE_2_TARGET_TEMPERATURE = "zone_2_target_temperature"
PROPERTY_ZONE_1_TARGET_HEAT_FLOW_TEMPERATURE = "zone_1_target_heat_flow_temperature"
PROPERTY_ZONE_2_TARGET_HEAT_FLOW_TEMPERATURE = "zone_2_target_heat_flow_temperature"
PROPERTY_ZONE_1_TARGET_COOL_FLOW_TEMPERATURE = "zone_1_target_heat_cool_temperature"
PROPERTY_ZONE_2_TARGET_COOL_FLOW_TEMPERATURE = "zone_2_target_heat_cool_temperature"
PROPERTY_ZONE_1_OPERATION_MODE = "zone_1_operation_mode"
PROPERTY_ZONE_2_OPERATION_MODE = "zone_2_operation_mode"

OPERATION_MODE_AUTO = "auto"
OPERATION_MODE_FORCE_HOT_WATER = "force_hot_water"

STATUS_IDLE = "idle"
STATUS_HEAT_WATER = "heat_water"
STATUS_HEAT_ZONES = "heat_zones"
STATUS_COOL = "cool"
STATUS_DEFROST = "defrost"
STATUS_STANDBY = "standby"
STATUS_LEGIONELLA = "legionella"
STATUS_UNKNOWN = "unknown"

_STATE_LOOKUP = {
    0: STATUS_IDLE,
    1: STATUS_HEAT_WATER,
    2: STATUS_HEAT_ZONES,
    3: STATUS_COOL,
    4: STATUS_DEFROST,
    5: STATUS_STANDBY,
    6: STATUS_LEGIONELLA,
}


_ZONE_INT_MODE_HEAT_THERMOSTAT = 0
_ZONE_INT_MODE_HEAT_FLOW = 1
_ZONE_INT_MODE_CURVE = 2
_ZONE_INT_MODE_COOL_THERMOSTAT = 3
_ZONE_INT_MODE_COOL_FLOW = 4

ZONE_OPERATION_MODE_HEAT_THERMOSTAT = "heat-thermostat"
ZONE_OPERATION_MODE_COOL_THERMOSTAT = "cool-thermostat"
ZONE_OPERATION_MODE_HEAT_FLOW = "heat-flow"
ZONE_OPERATION_MODE_COOL_FLOW = "cool-flow"
ZONE_OPERATION_MODE_CURVE = "curve"
ZONE_OPERATION_MODE_UNKNOWN = "unknown"
_ZONE_OPERATION_MODE_LOOKUP = {
    _ZONE_INT_MODE_HEAT_THERMOSTAT: ZONE_OPERATION_MODE_HEAT_THERMOSTAT,
    _ZONE_INT_MODE_HEAT_FLOW: ZONE_OPERATION_MODE_HEAT_FLOW,
    _ZONE_INT_MODE_CURVE: ZONE_OPERATION_MODE_CURVE,
    _ZONE_INT_MODE_COOL_THERMOSTAT: ZONE_OPERATION_MODE_COOL_THERMOSTAT,
    _ZONE_INT_MODE_COOL_FLOW: ZONE_OPERATION_MODE_COOL_FLOW,
}
_REVERSE_ZONE_OPERATION_MODE_LOOKUP = {
    value: key for key, value in _ZONE_OPERATION_MODE_LOOKUP.items()
}

ZONE_STATUS_HEAT = "heat"
ZONE_STATUS_IDLE = "idle"
ZONE_STATUS_COOL = "cool"
ZONE_STATUS_UNKNOWN = "unknown"


class Zone:
    """Zone controlled by Air-to-Water device."""

    def __init__(
        self,
        device,
        device_state: Callable[[], Optional[Dict[Any, Any]]],
        device_conf: Callable[[], Dict[Any, Any]],
        zone_index: int,
    ):
        """Initialize Zone."""
        self._device = device
        self._device_state = device_state
        self._device_conf = device_conf
        self.zone_index = zone_index

    @property
    def name(self) -> Optional[str]:
        """Return zone name.

        If a name is not defined, a name is generated using format "Zone n" where "n"
        is the number of the zone.
        """
        zone_name = self._device_conf().get(f"Zone{self.zone_index}Name")
        if zone_name is None:
            return f"Zone {self.zone_index}"
        return zone_name

    @property
    def prohibit(self) -> Optional[bool]:
        """Return prohibit flag of the zone."""
        state = self._device_state()
        if state is None:
            return None
        return state.get(f"ProhibitZone{self.zone_index}")

    @property
    def status(self) -> str:
        """Return the current status.

        This is a Air-to-Water device specific property. The value can be - depending
        on the device capabilities - "heat", "cool" or "idle".
        """
        state = self._device_state()
        if state is None:
            return ZONE_STATUS_UNKNOWN
        if state.get(f"IdleZone{self.zone_index}", False):
            return ZONE_STATUS_IDLE

        op_mode = self.operation_mode
        if op_mode in [
            ZONE_OPERATION_MODE_HEAT_THERMOSTAT,
            ZONE_OPERATION_MODE_HEAT_FLOW,
            ZONE_OPERATION_MODE_CURVE,
        ]:
            return ZONE_STATUS_HEAT
        if op_mode in [
            ZONE_OPERATION_MODE_COOL_THERMOSTAT,
            ZONE_OPERATION_MODE_COOL_FLOW,
        ]:
            return ZONE_STATUS_COOL

        return ZONE_STATUS_UNKNOWN

    @property
    def room_temperature(self) -> Optional[float]:
        """Return room temperature."""
        state = self._device_state()
        if state is None:
            return None
        return state.get(f"RoomTemperatureZone{self.zone_index}")

    @property
    def target_temperature(self) -> Optional[float]:
        """Return target temperature."""
        state = self._device_state()
        if state is None:
            return None
        return state.get(f"SetTemperatureZone{self.zone_index}")

    async def set_target_temperature(self, target_temperature):
        """Set target temperature for this zone."""
        if self.zone_index == 1:
            prop = PROPERTY_ZONE_1_TARGET_TEMPERATURE
        else:
            prop = PROPERTY_ZONE_2_TARGET_TEMPERATURE
        await self._device.set({prop: target_temperature})

    @property
    def flow_temperature(self) -> float:
        """Return current flow temperature.

        This value is not available in the standard state poll response. The poll
        update frequency can be a little bit lower that expected.
        """
        return self._device_conf()["Device"]["FlowTemperature"]

    @property
    def return_temperature(self) -> float:
        """Return current return flow temperature.

        This value is not available in the standard state poll response. The poll
        update frequency can be a little bit lower that expected.
        """
        return self._device_conf()["Device"]["ReturnTemperature"]

    @property
    def target_flow_temperature(self) -> Optional[float]:
        """Return target flow temperature of the currently active operation mode."""
        op_mode = self.operation_mode
        if op_mode is None:
            return None

        if op_mode in [
            ZONE_OPERATION_MODE_COOL_THERMOSTAT,
            ZONE_OPERATION_MODE_COOL_FLOW,
        ]:
            return self.target_cool_flow_temperature

        return self.target_heat_flow_temperature

    @property
    def target_heat_flow_temperature(self) -> Optional[float]:
        """Return target heat flow temperature."""
        state = self._device_state()
        if state is None:
            return None

        return state.get(f"SetHeatFlowTemperatureZone{self.zone_index}")

    @property
    def target_cool_flow_temperature(self) -> Optional[float]:
        """Return target cool flow temperature."""
        state = self._device_state()
        if state is None:
            return None

        return state.get(f"SetCoolFlowTemperatureZone{self.zone_index}")

    async def set_target_flow_temperature(self, target_flow_temperature):
        """Set target flow temperature for the currently active operation mode."""
        op_mode = self.operation_mode
        if op_mode is None:
            return None

        if op_mode in [
            ZONE_OPERATION_MODE_COOL_THERMOSTAT,
            ZONE_OPERATION_MODE_COOL_FLOW,
        ]:
            await self.set_target_cool_flow_temperature(target_flow_temperature)
        else:
            await self.set_target_heat_flow_temperature(target_flow_temperature)

    async def set_target_heat_flow_temperature(self, target_flow_temperature):
        """Set target heat flow temperature of this zone."""
        if self.zone_index == 1:
            prop = PROPERTY_ZONE_1_TARGET_HEAT_FLOW_TEMPERATURE
        else:
            prop = PROPERTY_ZONE_2_TARGET_HEAT_FLOW_TEMPERATURE
        await self._device.set({prop: target_flow_temperature})

    async def set_target_cool_flow_temperature(self, target_flow_temperature):
        """Set target cool flow temperature of this zone."""
        if self.zone_index == 1:
            prop = PROPERTY_ZONE_1_TARGET_COOL_FLOW_TEMPERATURE
        else:
            prop = PROPERTY_ZONE_2_TARGET_COOL_FLOW_TEMPERATURE
        await self._device.set({prop: target_flow_temperature})

    @property
    def operation_mode(self) -> Optional[str]:
        """Return current operation mode."""
        state = self._device_state()
        if state is None:
            return None

        print(state)

        mode = state.get(f"OperationModeZone{self.zone_index}")
        if not isinstance(mode, int):
            raise ValueError(f"Invalid operation mode [{mode}]")

        return _ZONE_OPERATION_MODE_LOOKUP.get(
            mode,
            ZONE_OPERATION_MODE_UNKNOWN,
        )

    @property
    def operation_modes(self) -> List[str]:
        """Return list of available operation modes."""
        modes = []
        device = self._device_conf().get("Device", {})
        if device.get("CanHeat", False):
            modes += [
                ZONE_OPERATION_MODE_HEAT_THERMOSTAT,
                ZONE_OPERATION_MODE_HEAT_FLOW,
                ZONE_OPERATION_MODE_CURVE,
            ]
        if device.get("CanCool", False):
            modes += [
                ZONE_OPERATION_MODE_COOL_THERMOSTAT,
                ZONE_OPERATION_MODE_COOL_FLOW,
            ]
        return modes

    async def set_operation_mode(self, mode: str):
        """Change operation mode."""
        state = self._device_state()
        if state is None:
            return

        int_mode = _REVERSE_ZONE_OPERATION_MODE_LOOKUP.get(mode)
        if int_mode is None:
            raise ValueError(f"Invalid mode '{mode}'")

        if self.zone_index == 1:
            prop = PROPERTY_ZONE_1_OPERATION_MODE
        else:
            prop = PROPERTY_ZONE_2_OPERATION_MODE

        await self._device.set({prop: int_mode})


class AtwDevice(Device):
    """Air-to-Water device."""

    def apply_write(self, state: Dict[str, Any], key: str, value: Any):
        """Apply writes to state object."""
        flags = state.get(EFFECTIVE_FLAGS, 0)

        if key == PROPERTY_TARGET_TANK_TEMPERATURE:
            state["SetTankWaterTemperature"] = value
            flags |= 0x1000000000020
        elif key == PROPERTY_OPERATION_MODE:
            state["ForcedHotWaterMode"] = value == OPERATION_MODE_FORCE_HOT_WATER
            flags |= 0x10000
        elif key == PROPERTY_ZONE_1_TARGET_TEMPERATURE:
            state["SetTemperatureZone1"] = value
            flags |= 0x200000080
        elif key == PROPERTY_ZONE_2_TARGET_TEMPERATURE:
            state["SetTemperatureZone2"] = value
            flags |= 0x800000200
        elif key == PROPERTY_ZONE_1_TARGET_HEAT_FLOW_TEMPERATURE:
            state["SetHeatFlowTemperatureZone1"] = value
            flags |= 0x1000000000000
        elif key == PROPERTY_ZONE_1_TARGET_COOL_FLOW_TEMPERATURE:
            state["SetCoolFlowTemperatureZone1"] = value
            flags |= 0x1000000000000
        elif key == PROPERTY_ZONE_2_TARGET_HEAT_FLOW_TEMPERATURE:
            state["SetHeatFlowTemperatureZone2"] = value
            flags |= 0x1000000000000
        elif key == PROPERTY_ZONE_2_TARGET_COOL_FLOW_TEMPERATURE:
            state["SetCoolFlowTemperatureZone2"] = value
            flags |= 0x1000000000000
        elif key == PROPERTY_ZONE_1_OPERATION_MODE:
            state["OperationModeZone1"] = value
            flags |= 0x08
        elif key == PROPERTY_ZONE_2_OPERATION_MODE:
            state["OperationModeZone2"] = value
            flags |= 0x10
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
        """Return minimum target tank water temperature.

        The value does not seem to be available on the API. A fixed value is used
        instead.
        """
        return 40.0

    @property
    def target_tank_temperature_max(self) -> Optional[float]:
        """Return maximum target tank water temperature.

        This value can be set using PROPERTY_TARGET_TANK_TEMPERATURE.
        """
        device = self._device_conf.get("Device", {})
        return device.get("MaxTankTemperature")

    @property
    def outside_temperature(self) -> Optional[float]:
        """Return outdoor temperature reported by the device.

        Outside temperature sensor cannot be complimented on its precision or sample
        rate. The value is reported using 1°C (2°F?) accuracy and updated every 2
        hours.
        """
        if self._state is None:
            return None
        return self._state.get("OutdoorTemperature")

    @property
    def zones(self) -> Optional[List[Zone]]:
        """Return zones controlled by this device.

        Zones without a thermostat are not returned.
        """
        _zones = []

        device = self._device_conf.get("Device", {})
        if device.get("HasThermostatZone1", False):
            _zones.append(Zone(self, lambda: self._state, lambda: self._device_conf, 1))

        if device.get("HasZone2") and device.get("HasThermostatZone2", False):
            _zones.append(Zone(self, lambda: self._state, lambda: self._device_conf, 2))

        return _zones

    @property
    def status(self) -> Optional[str]:
        """Return current state.

        This is a Air-to-Water device specific property. MELCloud uses "OperationMode"
        to indicate what the device is currently doing to meet its control values.
        """
        if self._state is None:
            return STATUS_UNKNOWN
        return _STATE_LOOKUP.get(self._state.get("OperationMode", -1), STATUS_UNKNOWN)

    @property
    def operation_mode(self) -> Optional[str]:
        """Return active operation mode.

        This value can be set using PROPERTY_OPERATION_MODE.
        """
        if self._state is None:
            return None
        if self._state.get("ForcedHotWaterMode", False):
            return OPERATION_MODE_FORCE_HOT_WATER
        return OPERATION_MODE_AUTO

    @property
    def operation_modes(self) -> List[str]:
        """Return available operation modes."""
        return [OPERATION_MODE_AUTO, OPERATION_MODE_FORCE_HOT_WATER]

    @property
    def holiday_mode(self) -> Optional[bool]:
        """Return holiday mode status."""
        if self._state is None:
            return None
        return self._state.get("HolidayMode", False)
