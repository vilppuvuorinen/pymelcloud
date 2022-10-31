# pymelcloud

[![PyPI version](https://badge.fury.io/py/pymelcloud.svg)](https://badge.fury.io/py/pymelcloud)

This is a package for interacting with MELCloud and Mitsubishi Electric
devices. It's still a little rough around the edges and the documentation
is non-existent.

The goals for this package are:

* To control and automate devices, not to configure them.
* Handle device capabilities behind the scenes.
* Make the different device types behave in predictable way.

## Notes on usage

There are built-in rate limits and debouncing for most of the methods
with the exception of the `Device` `update` method.

* Initialize devices for each account only once during application
runtime.
* Make sure the `update` calls for each `Device` are rate limited. A 60
second update interval is a good starting point. Going much faster will
exceed the expected load for MELCloud and can potentially cause
availability issues.
* Make absolutely sure the `update` calls are rate limited.

## Supported devices

* Air-to-air heat pumps (DeviceType=0)
* Air-to-water heat pumps (DeviceType=1)
* Energy Recovery Ventilators (DeviceType=3) 

## Read

Reads access only locally cached state. Call `device.update()` to
fetch the latest state.

Available properties:

* `name`
* `mac`
* `serial`
* `units` - model info of related units.
* `temp_unit`
* `last_seen`
* `power`
* `daily_energy_consumed`
* `wifi_signal`


Other properties are available through `_` prefixed state objects if
one has the time to go through the source.

### Air-to-air heat pump properties
* `room_temperature`
* `target_temperature`
* `target_temperature_step`
* `target_temperature_min`
* `target_temperature_max`
* `operation_mode`
* available `operation_modes`
* `fan_speed`
* available `fan_speeds`
* `vane_horizontal`
* available `vane_horizontal_positions`
* `vane_vertical`
* available `vane_vertical_positions`
* `total_energy_consumed` in kWh. See [notes below.](#energy-consumption)

### Air-to-water heat pump properties
* `tank_temperature`
* `target_tank_temperature`
* `tank_temperature_min`
* `tank_temperature_max`
* `outside_temperature`
* `zones`
  * `name`
  * `status`
  * `room_temperature`
  * `target_temperature`
* `status`
* `operation_mode`
* available `operation_modes`

### Energy recovery ventilator properties
* `room_temperature`
* `outdoor_temperature`
* available `fan_speeds`
* `fan_speed`
* `actual_supply_fan_speed`
* `actual_exhaust_fan_speed`
* available `ventilation_modes`
* `ventilation_mode`
* `actual_ventilation_mode`
* `total_energy_consumed`
* `wifi_signal`
* `presets`
* `error_code`
* `core_maintenance_required`
* `filter_maintenance_required`
* `night_purge_mode`
* `room_co2_level`

### Energy consumption

The energy consumption reading is a little strange. The API returns a
value of 1.8e6 for my unit. Judging by the scale the unit is either kJ
or Wh. However, neither of them quite fits.

* Total reading in kJ matches better what I would expect based on the
energy reports in MELCloud.
* In Wh the reading is 3-5 times greater than what I would expect, but
the reading is increasing at a rate that seems to match energy reports
in MELCloud.

Here are couple of readings with monthly reported usage as reference:

* 2020-01-04T23:42:00+02:00 - 1820400, 28.5 kWh
* 2020-01-05T09:44:00+02:00 - 1821300, 29.4 kWh
* 2020-01-05T10:49:00+02:00 - 1821500, 29.6 kWh

I'd say it's pretty clear that it is Wh and the total reading is not
reflective of unit lifetime energy consumption. `total_energy_consumed`
converts Wh to kWh.

## Write

Writes are applied after a debounce and update the local state once
completed. The physical device does not register the changes
immediately due to the 60 second polling interval.

To change a device's properties, call `device.set` with a Dict of the
new property values, for example: `await device.set({"fan_speed": "1"})`.

Writable properties are:

* `power`

### Air-to-air heat pump write

* `target_temperature`
* `operation_mode`
* `fan_speed`
* `vane_horizontal`
* `vane_vertical`

There's weird behavior associated with the horizontal vane swing.
Toggling it on will also toggle vertical swing on and the horizontal
swing has to be disabled before vertical vanes can be adjusted to any
other position. This behavior can be replicated using the MELCloud user
inteface.

### Air-to-water heat pump write

* `target_tank_temperature`
* `operation_mode`
* `zone_1_target_temperature`
* `zone_2_target_tempeature`

Zone target temperatures can also be set via the `Zone` object
returned by `zones` property on `AtwDevice`.

### Energy recovery ventilator write

* `ventilation_mode`
* `fan_speed`

## Example usage

```python
import aiohttp
import asyncio
import pymelcloud


async def main():

    async with aiohttp.ClientSession() as session:
        # call the login method with the session
        token = await pymelcloud.login("my@example.com", "mysecretpassword", session=session)

        # lookup the device
        devices = await pymelcloud.get_devices(token, session=session)
        device = devices[pymelcloud.DEVICE_TYPE_ATW][0]

        # perform logic on the device
        await device.update()

        print(device.name)
        await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```
