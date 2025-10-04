# Green Planet Energy API

[![PyPI version](https://badge.fury.io/py/greenplanet-energy-api.svg)](https://badge.fury.io/py/greenplanet-energy-api)
[![Python Support](https://img.shields.io/pypi/pyversions/greenplanet-energy-api.svg)](https://pypi.org/project/greenplanet-energy-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python API client for retrieving electricity pricing data from Green Planet Energy, a German renewable energy provider.

This library is primarily designed for use with Home Assistant but can be used in any Python project that needs access to Green Planet Energy pricing data.

## Features

- Async/await support
- Fetch hourly electricity prices for today and tomorrow
- Handles German decimal formatting
- Comprehensive error handling
- Type hints for better IDE support
- Lightweight with minimal dependencies

## Installation

```bash
pip install greenplanet-energy-api
```

## Quick Start

```python
import asyncio
from greenplanet_energy_api import GreenPlanetEnergyAPI

async def main():
    async with GreenPlanetEnergyAPI() as api:
        # Get electricity prices for today and tomorrow
        prices = await api.get_electricity_prices()

        # Access today's prices
        for hour in range(24):
            price_key = f"gpe_price_{hour:02d}"
            if price_key in prices:
                print(f"Hour {hour:02d}: {prices[price_key]} €/kWh")

        # Access tomorrow's prices
        for hour in range(24):
            price_key = f"gpe_price_{hour:02d}_tomorrow"
            if price_key in prices:
                print(f"Tomorrow Hour {hour:02d}: {prices[price_key]} €/kWh")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### GreenPlanetEnergyAPI

The main API client class.

#### Methods

- `async get_electricity_prices() -> dict[str, float]`: Fetch electricity prices for today and tomorrow
- `async close()`: Close the HTTP session
- Context manager support for automatic cleanup

#### Response Format

The API returns a dictionary with the following keys:

- `gpe_price_00` to `gpe_price_23`: Today's hourly prices (€/kWh)
- `gpe_price_00_tomorrow` to `gpe_price_23_tomorrow`: Tomorrow's hourly prices (€/kWh)

## Error Handling

The library raises the following exceptions:

- `GreenPlanetEnergyError`: Base exception class
- `GreenPlanetEnergyConnectionError`: Network/connection issues
- `GreenPlanetEnergyAPIError`: API-specific errors

## Development

### Setup

```bash
git clone https://github.com/petschni/greenplanet-energy-api.git
cd greenplanet-energy-api
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black src tests
ruff check src tests
mypy src
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/petschni/greenplanet-energy-api/issues) page
2. Create a new issue if needed
3. For Home Assistant related issues, please use the [Home Assistant Core Issues](https://github.com/home-assistant/core/issues) with the `green_planet_energy` label

## Disclaimer

This library is not officially associated with Green Planet Energy. It uses publicly available endpoints for retrieving pricing data.
