# Changelog

All notable changes to the Levolor PG3x plugin will be documented in this file.

## [1.0.5] - 2026-09-13

### Added
- Added binary `ST` status for UD Mobile switch-widget support.
- Added `GV5` Blind State with Open, Partially Open, and Closed states.
- Added separate locking for user commands and background status updates.

### Changed
- Binary Status reports Open for positions 0-50% and Closed for positions 51-100%.
- Open, Close, Stop, and Set Position commands are no longer delayed by slow background status queries.
- Normal whole-blind polling aborts when rapid polling becomes active, improving position-update responsiveness while a blind is moving.
- Retained standard `DON` and `DOF` command definitions so the UD Mobile Switch Widget operates correctly in both directions.

## [1.0.4] - 2026-09-13

### Added
- Added standard IoX `DON` and `DOF` commands for blind control.
  - `DON` closes the blind.
  - `DOF` opens the blind.
- Added user-facing **Close** and **Open** labels for the `DON` and `DOF` commands.
- Added position labels:
  - `0%` displays as **Open**.
  - `100%` displays as **Closed**.
  - Intermediate positions continue to display as percentages.
- Added rapid position polling after Open, Close, and Set Position commands.
  - Polls approximately every 10 seconds.
  - Stops when the requested position is confirmed.
  - Times out after approximately 3 minutes.
- Added support for simultaneous rapid polling of multiple moving blinds.
- Added per-blind rapid-poll cancellation so a new movement command supersedes the previous target.
- Stop command now cancels any outstanding rapid-poll target.

### Changed
- Serialized MotionBlinds gateway operations to prevent simultaneous gateway transactions.
- Normal whole-system short polling is temporarily skipped while rapid position polling is active, preventing slow polling of other blinds from delaying status updates for moving blinds.
- Improved position feedback in the Admin Console and UD Mobile during blind movement.

## [1.0.3]

### Changed
- Development version used while adding IoX `DON`/`DOF` support and Open/Close controls.
- Changes were incorporated into 1.0.4.

## [1.0.2]

### Added
- Added blind position reporting using `GV4`.
- Added Set Position command.
- Blind nodes report:
  - Position
  - Battery level
  - RSSI
  - Availability

### Changed
- Improved Levolor gateway and blind status handling.

## [1.0.1]

### Changed
- Early reliability and configuration improvements following initial testing.

## [1.0.0]

### Added
- Initial release.
- Levolor InMotion/MotionBlinds gateway support.
- Automatic blind discovery.
- Open, Close, Stop, and Query commands.
- Battery level reporting.
- RSSI reporting.
- Availability reporting.
- Configurable `gateway_ip` and `gateway_key`.
- Periodic blind status polling.
