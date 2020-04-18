# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Use fixed tank temperature minimum.

## [2.5.1] - 2020-04-05
### Fixed
- Map Atw zone `"curve"` mode to `heat` zone operation mode.

## [2.5.0] - 2020-04-05
### Added
- Add `cool` operation mode to `AtwDevice` zones.
- Add zone flow and flow return temperature read.

## [2.4.1] - 2020-03-29
### Fixed
- Fix search for devices assigned to Structure/Areas.

## [2.4.0] - 2020-02-20
### Changed
- Update `User-Agent`.
- Rename Atw status `"off"` to `"idle"`.

### Removed
- Remove `holiday_mode` set logic after testing with real devices.

## [2.3.0] - 2020-02-17
### Added
- Add a settable `holiday_mode` property to `AtwDevice`.

## [2.2.0] - 2020-02-17
### Changed
- Return same device types from `get_devices` and `Device` `device_type`.
- Use `MaxTankTemperature` as maximum target tank temperature and
calculate minimum using the previously used `MaxSetTemperature` and
`MinSetTemperature`.
- Remove keyword arguments from `login`. These values are not retained
after the function call.

### Fixed
- Make `AtwDevice` `status` consistent in out of sync state.

## [2.1.0] - 2020-02-14
### Added
- Add `temperature_increment` property to `Device`.
- Add `has_energy_consumed_meter` property to `AtaDevice`.

### Changed
- Forward AtaDevice `target_temperature_step` calls to
`temperature_increment`.
- Rename ATW zone `state` to `status`.
- Rename ATW `state` to `status`.
- Return heat statuses to `heat_zones` and `heat_water`

### Fixed
- Fix `get_devices` type hints.
- Fix `conf_update_interval` and `device_set_debounce` forwarding in `login`.
- Fix detached ATW zone state.
- Convert zone operation mode set to no-op instead of raising `ValueError`.
- Fix ATW zone name fallback.
- Add `None` state guards to ATW zone properties.

## [2.0.0] - 2020-02-08
### Added
- Experimental operation mode logic for ATW zones.

### Changed
- Use device type specific set endpoint.
- Return devices in a device type keyed dict from `get_devices` so that
caller does not have to do `isinstance` based filtering.

## [1.2.0] - 2020-01-30
### Changed
- Removed slug from fan speeds.

## [1.1.0] - 2020-01-30
### Changed
- Use underscores instead of dashes in state constants.

## [1.0.1] - 2020-01-29
### Fixed
- Remove invalid assertion from fan speed conversion.

## [1.0.0] - 2020-01-29
### Added
- `get_devices` module method. `Client` does not need to be accessed
directly anymore.

### Changed
- Support for multiple device types. Implemented `AtaDevice` (previous
implementation) and `AtwDevice`.
- `operation_modes`, `fan_speeds` and other list getters are
implemented as properties.
- `login` method returns only acquired access token.

## [0.7.1] - 2020-01-13
### Fixed
- Base `EffectiveFlags` update on current state and apply only new
flags.
- Use longer device write and conf update intervals.
- Fix target temperature flag logic.

## [0.7.0] - 2020-01-11
### Changed
- Moved login method to module. Original staticmethod implementation
is still available and forwards calls to the module method.

## [0.6.0] - 2020-01-11
### Added
- Token exposed as a property.

### Changed
- Removed destruct.

## [0.5.1] - 2020-01-05
### Fixed
- Removed `TypedDict` usage to support Python <3.8.

## [0.5.0] - 2020-01-05
### Added
- `total_energy_consumed` property returning kWh counter reading.
- `units` model information.

## [0.4.0] - 2019-12-30
### Added
- Horizontal and vertical vane support.

## [0.3.0] - 2019-12-27
### Changed
- Use proper async `set` function for `Device`. `asyncio.Event` is used
to signal a in-progress `set` operation. Multiple calls to `set` will
all wait for the same event that is set when the eventual write has been performed.

## [0.2.0] - 2019-12-26
### Fixed
- Return `None` when trying to read stale state instead of crashing.

## [0.1.1] - 2019-12-26
### Fixed
- Reset pending writes after they are applied to prevent rewriting them
on every subsequent write.

## [0.1.0] - 2019-12-25
Initial release
