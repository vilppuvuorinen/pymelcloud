# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Base `EffectiveFlags` update on current state and apply only new
flags.

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
