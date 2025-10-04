"""Green Planet Energy API client implementation."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from typing import Any

import aiohttp

from .exceptions import (
    GreenPlanetEnergyAPIError,
    GreenPlanetEnergyConnectionError,
)

_LOGGER = logging.getLogger(__name__)


class GreenPlanetEnergyAPI:
    """Client for Green Planet Energy API."""

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the API client.

        Args:
            session: Optional aiohttp session. If None, a new session will be created.
            timeout: Request timeout in seconds.
        """
        self._session = session
        self._own_session = session is None
        self._timeout = timeout
        self._api_url = "https://mein.green-planet-energy.de/p2"

    async def __aenter__(self) -> GreenPlanetEnergyAPI:
        """Enter async context manager."""
        if self._own_session:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP session if we own it."""
        if self._own_session and self._session:
            await self._session.close()
            self._session = None

    async def get_electricity_prices(self) -> dict[str, float]:
        """Fetch electricity prices for today and tomorrow.

        Returns:
            Dictionary with price data:
            - gpe_price_XX: Today's hourly prices (XX = 00-23)
            - gpe_price_XX_tomorrow: Tomorrow's hourly prices (XX = 00-23)

        Raises:
            GreenPlanetEnergyConnectionError: For network/connection issues
            GreenPlanetEnergyAPIError: For API-specific errors
        """
        if not self._session:
            raise GreenPlanetEnergyConnectionError("Session not initialized")

        today = date.today()
        tomorrow = today + timedelta(days=1)

        payload = {
            "jsonrpc": "2.0",
            "method": "getVerbrauchspreisUndWindsignal",
            "params": {
                "von": today.strftime("%Y-%m-%d"),
                "bis": tomorrow.strftime("%Y-%m-%d"),
                "aggregatsZeitraum": "",
                "aggregatsTyp": "",
                "source": "Portal",
            },
            "id": 564,
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/Latest Safari/537.36",
            "Referer": "https://mein.green-planet-energy.de/dynamischer-tarif/strompreise",
        }

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    self._api_url,
                    json=payload,
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        raise GreenPlanetEnergyAPIError(
                            f"API request failed with status {response.status}"
                        )

                    data = await response.json(content_type=None)
                    return self._process_response(data)

        except TimeoutError as err:
            raise GreenPlanetEnergyConnectionError(
                "Timeout while communicating with API"
            ) from err
        except aiohttp.ClientError as err:
            raise GreenPlanetEnergyConnectionError(
                f"Error communicating with API: {err}"
            ) from err

    def _process_response(self, response_data: dict[str, Any]) -> dict[str, float]:
        """Process the API response and extract hourly prices.

        Args:
            response_data: Raw API response data

        Returns:
            Processed price data dictionary

        Raises:
            GreenPlanetEnergyAPIError: For API-specific errors
        """
        processed_data: dict[str, float] = {}

        if "result" not in response_data:
            _LOGGER.warning("No result data in API response")
            return processed_data

        result = response_data["result"]

        # Check for API errors
        if result.get("errorCode", 0) != 0:
            error_text = result.get("errorText", "Unknown API error")
            raise GreenPlanetEnergyAPIError(
                f"API returned error: {error_text} (code: {result.get('errorCode')})"
            )

        # Get the time and price arrays
        datum_array = result.get("datum", [])
        wert_array = result.get("wert", [])

        if not datum_array or not wert_array or len(datum_array) != len(wert_array):
            _LOGGER.warning("Invalid or missing price data in API response")
            return processed_data

        # Process all data points from the API response
        for i, timestamp_str in enumerate(datum_array):
            try:
                # Parse timestamp string like "04.08.25, 09:00 Uhr"
                if " Uhr" not in timestamp_str:
                    continue

                # Extract hour part (e.g., "09:00" from "04.08.25, 09:00 Uhr")
                time_part = timestamp_str.split(", ")[1].replace(" Uhr", "")
                hour_str = time_part.split(":")[0]
                hour = int(hour_str)

                # Extract date part (e.g., "04.08.25" from "04.08.25, 09:00 Uhr")
                date_part = timestamp_str.split(", ")[0]

                # Get today and tomorrow dates in the same format
                today = date.today()
                tomorrow = today + timedelta(days=1)
                today_str = today.strftime("%d.%m.%y")
                tomorrow_str = tomorrow.strftime("%d.%m.%y")

                # Determine if this is today's or tomorrow's data
                if date_part == today_str:
                    # Today's price
                    hour_key = f"gpe_price_{hour:02d}"
                elif date_part == tomorrow_str:
                    # Tomorrow's price
                    hour_key = f"gpe_price_{hour:02d}_tomorrow"
                else:
                    # Unknown date, skip
                    continue

                # Convert price string to float (handle German decimal comma)
                price_str = wert_array[i]
                price_value = float(price_str.replace(",", "."))
                processed_data[hour_key] = price_value

            except (ValueError, IndexError) as err:
                _LOGGER.debug("Error parsing price data at index %s: %s", i, err)
                continue

        _LOGGER.debug("Processed electricity prices: %s", processed_data)
        return processed_data

    def get_highest_price_today(self, data: dict[str, float]) -> float | None:
        """Get the highest price for today.

        Args:
            data: Price data dictionary with hourly prices

        Returns:
            Highest price or None if no data available
        """
        if not data:
            return None

        today_prices = [
            price
            for key, price in data.items()
            if key.startswith("gpe_price_")
            and not key.endswith("_tomorrow")
            and price is not None
        ]

        return max(today_prices) if today_prices else None

    def get_lowest_price_day(self, data: dict[str, float]) -> float | None:
        """Get the lowest price during day hours (6-18) for today.

        Args:
            data: Price data dictionary with hourly prices

        Returns:
            Lowest day price or None if no data available
        """
        if not data:
            return None

        prices = []
        for hour in range(6, 18):  # Day period: 6:00 to 18:00
            price_key = f"gpe_price_{hour:02d}"
            if price_key in data:
                price = data[price_key]
                if price is not None:
                    prices.append(price)

        return min(prices) if prices else None

    def get_lowest_price_night(self, data: dict[str, float]) -> float | None:
        """Get the lowest price during night hours (18-6) for today/tonight.

        Args:
            data: Price data dictionary with hourly prices

        Returns:
            Lowest night price or None if no data available
        """
        if not data:
            return None

        prices = []
        # Evening hours today (18-23)
        for hour in range(18, 24):
            price_key = f"gpe_price_{hour:02d}"
            if price_key in data:
                price = data[price_key]
                if price is not None:
                    prices.append(price)

        # Early morning hours tomorrow (0-5)
        for hour in range(6):
            price_key = f"gpe_price_{hour:02d}_tomorrow"
            if price_key in data:
                price = data[price_key]
                if price is not None:
                    prices.append(price)

        return min(prices) if prices else None

    def get_current_price(self, data: dict[str, float], hour: int) -> float | None:
        """Get the current price for the specified hour.

        Args:
            data: Price data dictionary with hourly prices
            hour: Current hour (0-23)

        Returns:
            Current price or None if not available
        """
        if not data:
            return None

        price_key = f"gpe_price_{hour:02d}"
        return data.get(price_key)

    def get_highest_price_today_with_hour(
        self, data: dict[str, float]
    ) -> tuple[float | None, int | None]:
        """Get the highest price today and the hour when it occurs.

        Args:
            data: Price data dictionary with hourly prices

        Returns:
            Tuple of (highest_price, hour) or (None, None) if no data available
        """
        highest_price = self.get_highest_price_today(data)
        if highest_price is None or not data:
            return None, None

        for hour in range(24):
            price_key = f"gpe_price_{hour:02d}"
            if data.get(price_key) == highest_price:
                return highest_price, hour

        return highest_price, None

    def get_lowest_price_day_with_hour(
        self, data: dict[str, float]
    ) -> tuple[float | None, int | None]:
        """Get the lowest day price and the hour when it occurs.

        Args:
            data: Price data dictionary with hourly prices

        Returns:
            Tuple of (lowest_price, hour) or (None, None) if no data available
        """
        lowest_price = self.get_lowest_price_day(data)
        if lowest_price is None or not data:
            return None, None

        for hour in range(6, 18):  # Day period: 6:00 to 18:00
            price_key = f"gpe_price_{hour:02d}"
            if data.get(price_key) == lowest_price:
                return lowest_price, hour

        return lowest_price, None

    def get_lowest_price_night_with_hour(
        self, data: dict[str, float]
    ) -> tuple[float | None, int | None]:
        """Get the lowest night price and the hour when it occurs.

        Args:
            data: Price data dictionary with hourly prices

        Returns:
            Tuple of (lowest_price, hour) or (None, None) if no data available
        """
        lowest_price = self.get_lowest_price_night(data)
        if lowest_price is None or not data:
            return None, None

        # Check evening hours today (18-23)
        for hour in range(18, 24):
            price_key = f"gpe_price_{hour:02d}"
            if data.get(price_key) == lowest_price:
                return lowest_price, hour

        # Check early morning hours tomorrow (0-5)
        for hour in range(6):
            price_key = f"gpe_price_{hour:02d}_tomorrow"
            if data.get(price_key) == lowest_price:
                return lowest_price, hour

        return lowest_price, None
