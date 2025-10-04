"""Tests for GreenPlanetEnergyAPI."""

from datetime import date, timedelta

import aiohttp
import pytest
from aioresponses import aioresponses

from greenplanet_energy_api import (
    GreenPlanetEnergyAPI,
    GreenPlanetEnergyAPIError,
    GreenPlanetEnergyConnectionError,
)


@pytest.fixture
def mock_api_response():
    """Mock API response data."""
    # Use actual current date for testing
    today = date.today()
    tomorrow = today + timedelta(days=1)
    today_str = today.strftime("%d.%m.%y")
    tomorrow_str = tomorrow.strftime("%d.%m.%y")

    # Create datum array with proper timestamp format
    datum_array = [f"{today_str}, {hour:02d}:00 Uhr" for hour in range(24)]
    # Tomorrow's data
    datum_array.extend([f"{tomorrow_str}, {hour:02d}:00 Uhr" for hour in range(24)])

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


class TestPriceCalculationMethods:
    """Test price calculation helper methods."""

    @pytest.fixture
    def sample_price_data(self):
        """Sample price data for testing."""
        return {
            "gpe_price_00": 0.20,
            "gpe_price_01": 0.19,
            "gpe_price_02": 0.18,
            "gpe_price_03": 0.17,
            "gpe_price_04": 0.16,
            "gpe_price_05": 0.15,
            "gpe_price_06": 0.22,  # Day period starts
            "gpe_price_07": 0.24,
            "gpe_price_08": 0.26,
            "gpe_price_09": 0.28,
            "gpe_price_10": 0.30,
            "gpe_price_11": 0.32,
            "gpe_price_12": 0.31,
            "gpe_price_13": 0.29,
            "gpe_price_14": 0.27,
            "gpe_price_15": 0.25,
            "gpe_price_16": 0.23,
            "gpe_price_17": 0.21,  # Day period ends
            "gpe_price_18": 0.19,  # Night period starts
            "gpe_price_19": 0.17,
            "gpe_price_20": 0.15,
            "gpe_price_21": 0.16,
            "gpe_price_22": 0.18,
            "gpe_price_23": 0.20,
            "gpe_price_00_tomorrow": 0.14,
            "gpe_price_01_tomorrow": 0.13,
            "gpe_price_02_tomorrow": 0.12,
            "gpe_price_03_tomorrow": 0.11,
            "gpe_price_04_tomorrow": 0.10,  # Lowest night price
            "gpe_price_05_tomorrow": 0.11,
        }

    async def test_get_highest_price_today(self, sample_price_data):
        """Test getting highest price for today."""
        async with GreenPlanetEnergyAPI() as api:
            highest = api.get_highest_price_today(sample_price_data)
            assert highest == 0.32  # Hour 11

    async def test_get_lowest_price_day(self, sample_price_data):
        """Test getting lowest price during day hours (6-18)."""
        async with GreenPlanetEnergyAPI() as api:
            lowest = api.get_lowest_price_day(sample_price_data)
            assert lowest == 0.21  # Hour 17

    async def test_get_lowest_price_night(self, sample_price_data):
        """Test getting lowest price during night hours (18-6)."""
        async with GreenPlanetEnergyAPI() as api:
            lowest = api.get_lowest_price_night(sample_price_data)
            assert lowest == 0.10  # Hour 4 tomorrow

    async def test_get_current_price(self, sample_price_data):
        """Test getting current price for specific hour."""
        async with GreenPlanetEnergyAPI() as api:
            price_10 = api.get_current_price(sample_price_data, 10)
            assert price_10 == 0.30

    async def test_get_highest_price_today_with_hour(self, sample_price_data):
        """Test getting highest price with hour."""
        async with GreenPlanetEnergyAPI() as api:
            price, hour = api.get_highest_price_today_with_hour(sample_price_data)
            assert price == 0.32
            assert hour == 11

    async def test_get_lowest_price_day_with_hour(self, sample_price_data):
        """Test getting lowest day price with hour."""
        async with GreenPlanetEnergyAPI() as api:
            price, hour = api.get_lowest_price_day_with_hour(sample_price_data)
            assert price == 0.21
            assert hour == 17

    async def test_get_lowest_price_night_with_hour(self, sample_price_data):
        """Test getting lowest night price with hour."""
        async with GreenPlanetEnergyAPI() as api:
            price, hour = api.get_lowest_price_night_with_hour(sample_price_data)
            assert price == 0.10
            assert hour == 4

    async def test_empty_data(self):
        """Test methods with empty data."""
        async with GreenPlanetEnergyAPI() as api:
            assert api.get_highest_price_today({}) is None
            assert api.get_lowest_price_day({}) is None
            assert api.get_lowest_price_night({}) is None
            assert api.get_current_price({}, 10) is None
            assert api.get_highest_price_today_with_hour({}) == (None, None)
            assert api.get_lowest_price_day_with_hour({}) == (None, None)
            assert api.get_lowest_price_night_with_hour({}) == (None, None)
