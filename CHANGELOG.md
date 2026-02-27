# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.1] - 2026-02-26

### Fixed
- Fixed and issue with an empty array when loading the jobs page and returning i.map is not a function.

## [0.6.0] - 2026-02-26

### Added
- Pagination for Jobs endpoint. We'll likely hit a limit with sqlite in the future, in the meantime, delay this issue with pagination...
- This changelog.

### Changed
- Settings config dict ignores extra keys
