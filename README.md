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

Other properties are available through `_` prefixed state objects if
one has the time to go through the source. You definitely should go
through the source anyways. It's like under 500 lines.

## Write

Writes are applied after a debounce and update the local state once
completed. The physical device does not register the changes 
immediately due to the 60 second polling interval.

Writable properties are:

* `power`
* `target_temperature`
* `operation_mode`
* `fan_speed`

Vane control has not been implemented yet. The API cannot control
split vanes and home-assistant climate allows just selecting a _ swing_
mode. Long story short, I just skipped this feature for now.

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
