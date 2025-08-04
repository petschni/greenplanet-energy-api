# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
