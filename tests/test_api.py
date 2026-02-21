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
            # Tomorrow's prices (full 24 hours)
            "gpe_price_00_tomorrow": 0.14,
            "gpe_price_01_tomorrow": 0.13,
            "gpe_price_02_tomorrow": 0.12,
            "gpe_price_03_tomorrow": 0.11,
            "gpe_price_04_tomorrow": 0.10,  # Lowest night price
            "gpe_price_05_tomorrow": 0.11,
            "gpe_price_06_tomorrow": 0.19,  # Day period tomorrow
            "gpe_price_07_tomorrow": 0.21,
            "gpe_price_08_tomorrow": 0.23,
            "gpe_price_09_tomorrow": 0.25,
            "gpe_price_10_tomorrow": 0.27,
            "gpe_price_11_tomorrow": 0.29,
            "gpe_price_12_tomorrow": 0.28,
            "gpe_price_13_tomorrow": 0.26,
            "gpe_price_14_tomorrow": 0.24,
            "gpe_price_15_tomorrow": 0.22,
            "gpe_price_16_tomorrow": 0.20,
            "gpe_price_17_tomorrow": 0.18,
            "gpe_price_18_tomorrow": 0.16,
            "gpe_price_19_tomorrow": 0.15,
            "gpe_price_20_tomorrow": 0.14,
            "gpe_price_21_tomorrow": 0.15,
            "gpe_price_22_tomorrow": 0.17,
            "gpe_price_23_tomorrow": 0.19,
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
            assert api.get_cheapest_duration_day({}, 2.5) == (None, None)
            assert api.get_cheapest_duration_night({}, 2.5) == (None, None)

    async def test_get_cheapest_duration_day(self, sample_price_data):
        """Test getting cheapest duration during day hours."""
        async with GreenPlanetEnergyAPI() as api:
            # Test 2.5 hour window during day (6-18)
            avg_price, start_hour = api.get_cheapest_duration_day(
                sample_price_data, 2.5
            )
            assert avg_price is not None
            assert start_hour is not None
            # Should find a window starting around hour 15-17 (lowest prices in day)
            assert 15 <= start_hour <= 17

    async def test_get_cheapest_duration_night(self, sample_price_data):
        """Test getting cheapest duration during night hours."""
        async with GreenPlanetEnergyAPI() as api:
            # Test 2.5 hour window during night (18-6)
            avg_price, start_hour = api.get_cheapest_duration_night(
                sample_price_data, 2.5
            )
            assert avg_price is not None
            assert start_hour is not None
            # Should find a window in early morning (hours 2-4 tomorrow have lowest prices)
            assert start_hour in [2, 3, 4] or start_hour in [20, 21, 22]

    async def test_get_cheapest_duration_day_whole_hours(self, sample_price_data):
        """Test getting cheapest duration with whole hours."""
        async with GreenPlanetEnergyAPI() as api:
            # Test 3 hour window during day
            avg_price, start_hour = api.get_cheapest_duration_day(
                sample_price_data, 3.0
            )
            assert avg_price is not None
            assert start_hour is not None
            # Verify it's actually during day period
            assert 6 <= start_hour < 18

    async def test_get_cheapest_duration_invalid_duration(self, sample_price_data):
        """Test with invalid duration values."""
        async with GreenPlanetEnergyAPI() as api:
            # Zero duration
            assert api.get_cheapest_duration_day(sample_price_data, 0) == (None, None)
            # Negative duration
            assert api.get_cheapest_duration_day(sample_price_data, -1) == (None, None)
            # Duration longer than available period
            assert api.get_cheapest_duration_day(sample_price_data, 20) == (None, None)

    async def test_get_cheapest_duration_with_current_hour_filtering(
        self, sample_price_data
    ):
        """Test cheapest duration methods with current_hour filtering."""
        async with GreenPlanetEnergyAPI() as api:
            # Test day search when in day period (e.g., at 10:00)
            # Should filter out hours before 10:00
            avg_price, start_hour = api.get_cheapest_duration_day(
                sample_price_data, 3.0, current_hour=10
            )
            assert avg_price is not None
            assert start_hour is not None
            assert start_hour >= 10, "Should not return past hours from current day"
            assert start_hour < 18, "Should be within day period"

            # Test day search when outside day period (e.g., at 20:00)
            # Should use tomorrow's data
            avg_price, start_hour = api.get_cheapest_duration_day(
                sample_price_data, 3.0, current_hour=20
            )
            assert avg_price is not None
            assert start_hour is not None
            assert 6 <= start_hour < 18, "Should return tomorrow's day hours"

            # Test night search when in night period evening (e.g., at 20:00)
            # Should filter out hours 18-20
            avg_price, start_hour = api.get_cheapest_duration_night(
                sample_price_data, 3.0, current_hour=20
            )
            assert avg_price is not None
            assert start_hour is not None
            assert start_hour > 20 or start_hour < 6, (
                "Should not return hours 18-20 (past)"
            )

            # Test night search when in night period early morning (e.g., at 02:00)
            # Should filter out hours 18-23 (yesterday) and 0-2 (today)
            avg_price, start_hour = api.get_cheapest_duration_night(
                sample_price_data, 3.0, current_hour=2
            )
            assert avg_price is not None
            assert start_hour is not None
            assert start_hour > 2 or start_hour >= 18, "Should filter past hours 0-2"

            # Test night search when in day period (e.g., at 14:00)
            # Should return full upcoming night (no filtering)
            avg_price, start_hour = api.get_cheapest_duration_night(
                sample_price_data, 3.0, current_hour=14
            )
            assert avg_price is not None
            assert start_hour is not None
            # Should find cheapest in upcoming night (hours 18-23 or 0-5 tomorrow)

            # Test full day search with current_hour (e.g., at 14:00)
            # Should filter out hours 0-13
            avg_price, start_hour = api.get_cheapest_duration(
                sample_price_data, 3.0, current_hour=14
            )
            assert avg_price is not None
            assert start_hour is not None
            assert start_hour >= 14, "Should not return past hours"

    async def test_get_cheapest_duration_no_valid_windows(self):
        """Test when no valid windows exist due to filtering."""
        # Create data with only early hours
        test_data = {
            "gpe_price_00": 0.20,
            "gpe_price_01": 0.21,
            "gpe_price_02": 0.22,
            "gpe_price_03": 0.23,
        }

        async with GreenPlanetEnergyAPI() as api:
            # Try to get 3-hour window when at hour 23 (no future hours available)
            avg_price, start_hour = api.get_cheapest_duration(
                test_data, 3.0, current_hour=23
            )
            # Should return None because not enough future hours
            assert avg_price is None
            assert start_hour is None

    async def test_get_cheapest_duration_edge_cases(self, sample_price_data):
        """Test edge cases for current_hour filtering."""
        async with GreenPlanetEnergyAPI() as api:
            # Test at start of day period (6:00)
            avg_price, start_hour = api.get_cheapest_duration_day(
                sample_price_data, 2.0, current_hour=6
            )
            assert avg_price is not None
            assert start_hour >= 6

            # Test at end of day period (17:00)
            avg_price, start_hour = api.get_cheapest_duration_day(
                sample_price_data, 1.0, current_hour=17
            )
            assert avg_price is not None
            assert start_hour == 17  # Only hour 17 available for 1-hour duration

            # Test at start of night period (18:00)
            avg_price, start_hour = api.get_cheapest_duration_night(
                sample_price_data, 2.0, current_hour=18
            )
            assert avg_price is not None
            assert start_hour > 18 or start_hour < 6

            # Test at midnight (0:00) in night period
            avg_price, start_hour = api.get_cheapest_duration_night(
                sample_price_data, 2.0, current_hour=0
            )
            assert avg_price is not None
            assert start_hour > 0 or start_hour >= 18

    async def test_get_cheapest_duration_fractional_hours_with_filtering(
        self, sample_price_data
    ):
        """Test fractional duration with current_hour filtering."""
        async with GreenPlanetEnergyAPI() as api:
            # Test 2.5 hour window at hour 15 during day
            avg_price, start_hour = api.get_cheapest_duration_day(
                sample_price_data, 2.5, current_hour=15
            )
            assert avg_price is not None
            assert start_hour is not None
            assert start_hour >= 15, "Should respect current_hour filter"
            assert start_hour < 18, "Should be in day period"

            # Test 3.7 hour window at hour 19 during night
            avg_price, start_hour = api.get_cheapest_duration_night(
                sample_price_data, 3.7, current_hour=19
            )
            assert avg_price is not None
            assert start_hour is not None
            assert start_hour > 19 or start_hour < 6, "Should filter past hour 19"

    async def test_with_real_api_data_pattern(self):
        """Test with real API data pattern showing incomplete tomorrow data."""
        # Simulate processed data from real API response
        # where tomorrow (22.02.26) has complete 24h data
        real_data = {
            # Today (21.02.26) - last value from each hour's 15-min intervals
            "gpe_price_00": 0.2516,
            "gpe_price_01": 0.2327,
            "gpe_price_02": 0.2373,
            "gpe_price_03": 0.2562,
            "gpe_price_04": 0.2435,
            "gpe_price_05": 0.2473,
            "gpe_price_06": 0.2418,
            "gpe_price_07": 0.2516,
            "gpe_price_08": 0.2579,
            "gpe_price_09": 0.2434,
            "gpe_price_10": 0.2651,
            "gpe_price_11": 0.2636,
            "gpe_price_12": 0.2549,
            "gpe_price_13": 0.2713,
            "gpe_price_14": 0.2484,
            "gpe_price_15": 0.2492,
            "gpe_price_16": 0.2825,
            "gpe_price_17": 0.3024,
            "gpe_price_18": 0.3036,
            "gpe_price_19": 0.3248,
            "gpe_price_20": 0.3126,
            "gpe_price_21": 0.3004,  # Current time around here
            "gpe_price_22": 0.2906,
            "gpe_price_23": 0.3001,
            # Tomorrow (22.02.26) - complete 24h
            "gpe_price_00_tomorrow": 0.2539,
            "gpe_price_01_tomorrow": 0.2522,
            "gpe_price_02_tomorrow": 0.2496,
            "gpe_price_03_tomorrow": 0.2443,
            "gpe_price_04_tomorrow": 0.2476,
            "gpe_price_05_tomorrow": 0.2486,
            "gpe_price_06_tomorrow": 0.2616,
            "gpe_price_07_tomorrow": 0.2768,
            "gpe_price_08_tomorrow": 0.2881,
            "gpe_price_09_tomorrow": 0.3040,
            "gpe_price_10_tomorrow": 0.2954,
            "gpe_price_11_tomorrow": 0.2927,
            "gpe_price_12_tomorrow": 0.2751,
            "gpe_price_13_tomorrow": 0.2799,
            "gpe_price_14_tomorrow": 0.2645,
            "gpe_price_15_tomorrow": 0.2825,
            "gpe_price_16_tomorrow": 0.2668,
            "gpe_price_17_tomorrow": 0.2348,
        }

        async with GreenPlanetEnergyAPI() as api:
            # Test night search at 21:00 (should filter out 18-21, use 22-23 and tomorrow 0-5)
            avg_price, start_hour = api.get_cheapest_duration_night(
                real_data, 3.0, current_hour=21
            )
            assert avg_price is not None
            assert start_hour is not None
            # Should find cheapest in hours 22-23 or 0-5 tomorrow
            assert start_hour in [22, 23, 0, 1, 2, 3, 4], (
                f"Expected night hours after 21:00, got {start_hour}"
            )

            # Test day search at 21:00 (outside day period, should use tomorrow's day hours)
            avg_price, start_hour = api.get_cheapest_duration_day(
                real_data, 3.0, current_hour=21
            )
            assert avg_price is not None
            assert start_hour is not None
            assert 6 <= start_hour < 18, (
                f"Should use tomorrow's day hours, got {start_hour}"
            )

            # Test with incomplete tomorrow data (only hours 0-10)
            incomplete_data = {
                k: v
                for k, v in real_data.items()
                if not (k.endswith("_tomorrow") and int(k.split("_")[2]) > 10)
            }

            # Day search should still work with partial tomorrow data
            avg_price, start_hour = api.get_cheapest_duration_day(
                incomplete_data, 3.0, current_hour=21
            )
            assert avg_price is not None
            assert start_hour is not None
            assert 6 <= start_hour <= 10, "Should work with available tomorrow hours"
