import httpx

from app.extract.errors import ContentTypeError, HTTPError, NetworkError


async def fetch_content(url: str, timeout: int = 15) -> tuple[bytes | None, dict]:
    """
    Fetches raw content from a URL using httpx.

    Args:
        url (str): The URL to fetch.
        timeout (int): The timeout for the request in seconds.

    Returns:
        tuple[bytes | None, dict]: A tuple containing the raw content bytes and response metadata.
                                   Metadata includes 'status_code', 'headers', 'content_type'.

    Raises:
        NetworkError: For network-related issues (e.g., timeout, connection error).
        HTTPError: For non-2xx HTTP status codes.
        ContentTypeError: If the fetched content type is not text/html.
    """
    headers = {"User-Agent": "StorySpool-Bot/1.0 (+https://storyspool.com/bot)"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses

            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                raise ContentTypeError(
                    f"Unsupported content type: {content_type}. Expected text/html.",
                    error_code="UNSUPPORTED_CONTENT_TYPE",
                )

            return response.content, {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_type": content_type,
            }
    except httpx.TimeoutException as e:
        raise NetworkError(
            f"Request timed out for {url}: {e}", error_code="NETWORK_TIMEOUT"
        )
    except httpx.ConnectError as e:
        raise NetworkError(
            f"Connection error for {url}: {e}", error_code="CONNECTION_ERROR"
        )
    except httpx.RequestError as e:
        # Catch-all for other httpx request errors (e.g., DNS issues)
        raise NetworkError(f"Request error for {url}: {e}", error_code="REQUEST_ERROR")
    except httpx.HTTPStatusError as e:
        raise HTTPError(
            f"HTTP error {e.response.status_code} for {url}",
            status_code=e.response.status_code,
            error_code=f"HTTP_{e.response.status_code}",
        )
