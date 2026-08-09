# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Corrected the "Seer" rename from 0.6.2 to "Seerr" (the actual name of Overseerr's successor). `SEER_URL`/`SEER_API_KEY` environment variables are now `SEERR_URL`/`SEERR_API_KEY`; existing `services.seer_*` admin settings are migrated to `services.seerr_*` on upgrade.
- Console and file logs now include the fields passed via `extra=` on log calls (e.g. the underlying error on a failed request), instead of silently dropping them. Previously only the optional Loki handler surfaced this context, so failures were hard to diagnose without it enabled.

## [0.6.2] - 2026-08-08

### Changed
- Renamed the Overseerr integration to Seer (Overseerr's successor project) throughout the codebase, config, and docs. `OVERSEERR_URL`/`OVERSEERR_API_KEY` environment variables are now `SEER_URL`/`SEER_API_KEY`.
- Moved the extension/reminder DB stores out of `interface_adapters/gateways` into `frameworks_and_drivers/database` to match their role as SQLModel-backed stores rather than external-service gateways.
- `EmailNotificationService` now depends on an `IEmailClient` interface instead of the concrete FastMail-based client.

### Fixed
- Added a database migration so existing `services.overseerr_*` admin settings are renamed to `services.seer_*` on upgrade, instead of silently falling back to defaults.

## [0.6.1] - 2026-02-26

### Fixed
- Fixed and issue with an empty array when loading the jobs page and returning i.map is not a function.

## [0.6.0] - 2026-02-26

### Added
- Pagination for Jobs endpoint. We'll likely hit a limit with sqlite in the future, in the meantime, delay this issue with pagination...
- This changelog.

### Changed
- Settings config dict ignores extra keys
