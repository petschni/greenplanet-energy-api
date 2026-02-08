# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5] - 2026-02-08

### Added
- New `get_cheapest_duration_day()` method to find the cheapest consecutive period during day hours (6:00-18:00)
- New `get_cheapest_duration_night()` method to find the cheapest consecutive period during night hours (18:00-06:00)
- Support for fractional hour durations (e.g., 2.5 hours) in duration-based price calculations
- Sliding window algorithm for optimized consecutive period price calculations
- Comprehensive test coverage for duration-based price queries

### Changed
- Enhanced API with more flexible time-window based price queries
- Improved handling of overnight periods that wrap around midnight

## [0.1.4] - 2025-08-04

### Added
- Pre-commit hooks for code quality
- Comprehensive test suite improvements

## [0.1.3] - 2025-08-04

### Changed
- Moved calculation logic to API package

## [0.1.2] - 2025-08-04

### Fixed
- Fixed GitHub Actions workflow using deprecated release action
- Updated to use maintained `softprops/action-gh-release@v2`
- Improved release notes generation and formatting

### Changed
- Better PyPI version checking using JSON API instead of HTTP status codes
- More robust version detection for automated publishing

## [0.1.1] - 2025-08-04

### Fixed
- Fixed linting issues with black and ruff
- Updated pyproject.toml to use modern ruff configuration format
- Improved GitHub Actions workflow

### Added
- Comprehensive local testing script (`run_all_checks.sh`)
- Better documentation for development workflow

## [0.1.0] - 2025-08-04

### Added
- Initial release of Green Planet Energy API client
- Support for fetching hourly electricity prices
- Async/await support with aiohttp
- Comprehensive error handling
- Type hints for better IDE support
- Context manager support for automatic cleanup
- Support for both today and tomorrow price data
- German decimal format handling

### Features
- `GreenPlanetEnergyAPI` main client class
- `get_electricity_prices()` method for fetching price data
- Proper exception hierarchy with custom error classes
- Automatic session management

### Documentation
- Complete README with usage examples
- API reference documentation
- Development setup instructions
- Contributing guidelines

## [0.1.4] - 2025-10-04

### Added
- `get_highest_price_today(data)`: Get highest electricity price for today
- `get_lowest_price_day(data)`: Get lowest price during day hours (6-18) for today
- `get_lowest_price_night(data)`: Get lowest price during night hours (18-6) for today/tonight
- `get_current_price(data, hour)`: Get price for a specific hour
- `get_highest_price_today_with_hour(data)`: Get highest price and hour
- `get_lowest_price_day_with_hour(data)`: Get lowest day price and hour
- `get_lowest_price_night_with_hour(data)`: Get lowest night price and hour

### Note
- Day period prices use only today's data (6:00-18:00)
- Night period prices use today's evening (18:00-23:00) and tomorrow's early morning (00:00-05:00)
