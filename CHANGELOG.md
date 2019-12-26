# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2019-12-26
### Fixed
- Return `None` when trying to read stale state instead of crashing.

## [0.1.1] - 2019-12-26
### Fixed
- Reset pending writes after they are applied to prevent rewriting them
on every subsequent write.

## [0.1.0] - 2019-12-25
Initial release