"""Tests for GreenPlanetEnergyAPI."""

import pytest
from aioresponses import aioresponses
import aiohttp

from greenplanet_energy_api import (
    GreenPlanetEnergyAPI,
    GreenPlanetEnergyAPIError,
    GreenPlanetEnergyConnectionError,
)


@pytest.fixture
def mock_api_response():
    """Mock API response data."""
    # Create datum array with proper timestamp format
    datum_array = [f"04.08.25, {hour:02d}:00 Uhr" for hour in range(24)]
    # Tomorrow's data: "05.08.25, HH:00 Uhr"
    datum_array.extend([f"05.08.25, {hour:02d}:00 Uhr" for hour in range(24)])

    # Create wert array (prices as strings with German decimal comma format)
    # Today's prices: 0.20 + (hour * 0.01)
    wert_array = [f"{0.20 + (hour * 0.01):.2f}".replace(".", ",") for hour in range(24)]
    # Tomorrow's prices: 0.25 + (hour * 0.01) (slightly different for testing)
    wert_array.extend(
        [f"{0.25 + (hour * 0.01):.2f}".replace(".", ",") for hour in range(24)]
    )

    return {
        "result": {
            "errorCode": 0,
            "datum": datum_array,
            "wert": wert_array,
        }
    }


@pytest.fixture
def mock_api_error_response():
    """Mock API error response."""
    return {
        "result": {
            "errorCode": 1,
            "errorText": "API Error occurred",
        }
    }


class TestGreenPlanetEnergyAPI:
    """Test GreenPlanetEnergyAPI class."""

    async def test_context_manager(self):
        """Test context manager functionality."""
        async with GreenPlanetEnergyAPI() as api:
            assert api._session is not None
        # Session should be closed after context exit

    async def test_get_electricity_prices_success(self, mock_api_response):
        """Test successful electricity prices retrieval."""
        with aioresponses() as m:
            m.post(
                "https://mein.green-planet-energy.de/p2",
                payload=mock_api_response,
                status=200,
            )

            async with GreenPlanetEnergyAPI() as api:
                prices = await api.get_electricity_prices()

            # Should have 48 total prices (24 today + 24 tomorrow)
            assert len(prices) == 48

            # Check today's prices
            for hour in range(24):
                key = f"gpe_price_{hour:02d}"
                assert key in prices
                expected_price = round(0.20 + (hour * 0.01), 2)
                assert abs(prices[key] - expected_price) < 0.001

            # Check tomorrow's prices
            for hour in range(24):
                key = f"gpe_price_{hour:02d}_tomorrow"
                assert key in prices
                expected_price = round(0.25 + (hour * 0.01), 2)
                assert abs(prices[key] - expected_price) < 0.001

    async def test_get_electricity_prices_api_error(self, mock_api_error_response):
        """Test API error handling."""
        with aioresponses() as m:
            m.post(
                "https://mein.green-planet-energy.de/p2",
                payload=mock_api_error_response,
                status=200,
            )

            async with GreenPlanetEnergyAPI() as api:
                with pytest.raises(GreenPlanetEnergyAPIError) as exc_info:
                    await api.get_electricity_prices()

                assert "API Error occurred" in str(exc_info.value)

    async def test_get_electricity_prices_http_error(self):
        """Test HTTP error handling."""
        with aioresponses() as m:
            m.post(
                "https://mein.green-planet-energy.de/p2",
                status=500,
            )

            async with GreenPlanetEnergyAPI() as api:
                with pytest.raises(GreenPlanetEnergyAPIError) as exc_info:
                    await api.get_electricity_prices()

                assert "API request failed with status 500" in str(exc_info.value)

    async def test_get_electricity_prices_connection_error(self):
        """Test connection error handling."""
        with aioresponses() as m:
            m.post(
                "https://mein.green-planet-energy.de/p2",
                exception=aiohttp.ClientError("Connection failed"),
            )

            async with GreenPlanetEnergyAPI() as api:
                with pytest.raises(GreenPlanetEnergyConnectionError):
                    await api.get_electricity_prices()

    async def test_get_electricity_prices_timeout(self):
        """Test timeout handling."""
        async with GreenPlanetEnergyAPI(timeout=0.001) as api:
            with pytest.raises(GreenPlanetEnergyConnectionError) as exc_info:
                await api.get_electricity_prices()

            assert "Timeout" in str(exc_info.value)

    async def test_get_electricity_prices_invalid_response(self):
        """Test handling of invalid API response."""
        with aioresponses() as m:
            m.post(
                "https://mein.green-planet-energy.de/p2",
                payload={"invalid": "response"},
                status=200,
            )

            async with GreenPlanetEnergyAPI() as api:
                prices = await api.get_electricity_prices()
                assert len(prices) == 0  # Should return empty dict for invalid response

    async def test_session_not_initialized(self):
        """Test error when session is not initialized."""
        api = GreenPlanetEnergyAPI()
        with pytest.raises(GreenPlanetEnergyConnectionError) as exc_info:
            await api.get_electricity_prices()

        assert "Session not initialized" in str(exc_info.value)
