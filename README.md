# pymelcloud

This is a package for interacting with MELCloud and Mitsubishi Electric
HVAC devices, etc. It's still a little rough all around and the
documentation is a joke.

## Read

Reads access only locally cached state. Call `device.update()` to
fetch the latest state.

Available properties:

* `name`
* `mac`
* `serial`
* `units` - model info of related units.
* `temperature`
* `temp_unit`
* `last_seen`
* `power`
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

Other properties are available through `_` prefixed state objects if
one has the time to go through the source. You definitely should go
through the source anyways. It's like under ~~500~~ 600 lines.

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

Writable properties are:

* `power`
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

## Example usage

```python
>>> import pymelcloud
>>> client = pymelcloud.Client.login("user@example.com", "password")
>>> devices = await client.get_devices()
>>> device = devices[0]
>>> await device.update()
>>> device.name
'Heat Pump 1'
>>> device.target_temperature
21.0
>>> device.set({"target_temperature": 21.5})
>>> >>> device.target_temperature
21.5
```
