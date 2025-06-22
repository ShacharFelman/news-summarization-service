"""Exceptions for the fetchers app."""


class FetcherError(Exception):
    """Base exception for fetchers app."""
    pass


class ConfigurationError(FetcherError):
    """Raised when there's an issue with fetcher configuration."""
    pass


class APIError(FetcherError):
    """Raised when there's an error communicating with external APIs."""
    pass


class ValidationError(FetcherError):
    """Raised when there's an error validating data."""
    pass


class ProcessingError(FetcherError):
    """Raised when there's an error processing fetched articles."""
    pass


class RateLimitError(APIError):
    """Raised when a rate limit is exceeded."""
    pass
