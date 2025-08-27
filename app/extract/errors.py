class ExtractionError(Exception):
    """Base exception for all extraction-related errors."""

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.error_code = error_code


class NetworkError(ExtractionError):
    """Raised for network-related issues during fetching."""

    pass


class HTTPError(ExtractionError):
    """Raised for non-2xx HTTP status codes."""

    def __init__(self, message: str, status_code: int, error_code: str | None = None):
        super().__init__(message, error_code)
        self.status_code = status_code


class ContentTypeError(ExtractionError):
    """Raised when the fetched content type is not supported."""

    pass


class ParseError(ExtractionError):
    """Raised when content parsing fails or yields no meaningful data."""

    pass


class CanonicalizationError(ExtractionError):
    """Raised when URL canonicalization fails."""

    pass
