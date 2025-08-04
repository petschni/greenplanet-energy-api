"""Exceptions for Green Planet Energy API."""


class GreenPlanetEnergyError(Exception):
    """Base exception for Green Planet Energy API."""


class GreenPlanetEnergyConnectionError(GreenPlanetEnergyError):
    """Exception raised for connection errors."""


class GreenPlanetEnergyAPIError(GreenPlanetEnergyError):
    """Exception raised for API-specific errors."""
