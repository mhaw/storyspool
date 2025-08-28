import httpx
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.extract.errors import (
    ContentTypeError,
    HTTPError,
    NetworkError,
)


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
        # Try httpx first for speed and efficiency
        content, metadata = await _fetch_with_httpx(url, timeout, headers)
        return content, metadata
    except (NetworkError, HTTPError, ContentTypeError) as e:
        # Fallback to Playwright for more robust fetching, especially for JS-rendered content
        print(
            f"INFO: httpx failed for {url} ({e.error_code}). Falling back to Playwright."
        )
        try:
            content, metadata = await _fetch_with_playwright(url, timeout)
            return content, metadata
        except Exception as pe:
            raise NetworkError(
                f"Playwright fetch failed for {url}: {pe}",
                error_code="PLAYWRIGHT_FETCH_FAILED",
            ) from pe


async def _fetch_with_httpx(
    url: str, timeout: int, headers: dict
) -> tuple[bytes | None, dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses

        content_type = response.headers.get("Content-Type", "").lower()
        if "application/pdf" in content_type:
            return response.content, {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_type": content_type,
            }
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


async def _fetch_with_playwright(url: str, timeout: int) -> tuple[bytes | None, dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=timeout * 1000)  # Playwright timeout is in ms

            # Attempt to dismiss common cookie banners
            # This is a heuristic and might need to be expanded
            await page.evaluate(
                """
                const selectors = [
                    '#onetrust-accept-btn-handler',
                    '.cc-allow',
                    'button[id*="cookie"][id*="accept"]',
                    'button[class*="cookie"][class*="accept"]',
                    'button:has-text("Accept All")',
                    'button:has-text("Agree")'
                ];
                for (const selector of selectors) {
                    const button = document.querySelector(selector);
                    if (button) {
                        button.click();
                        console.log('Clicked cookie banner button:', selector);
                        break;
                    }
                }
            """
            )
            await page.wait_for_timeout(
                1000
            )  # Give some time for the banner to disappear

            content = await page.content()
            return content.encode("utf-8"), {
                "status_code": 200,  # Playwright doesn't give direct HTTP status for final page content
                "headers": {},  # Headers are not easily accessible for the final rendered page
                "content_type": "text/html; charset=utf-8",
            }
        except PlaywrightTimeoutError:
            raise NetworkError(
                f"Playwright timed out for {url}", error_code="PLAYWRIGHT_TIMEOUT"
            )
        except Exception as e:
            raise NetworkError(
                f"Playwright error for {url}: {e}", error_code="PLAYWRIGHT_ERROR"
            )
        finally:
            await browser.close()


# Re-raise httpx exceptions as custom errors for consistent handling
def _raise_httpx_error(e: httpx.RequestError, url: str):
    if isinstance(e, httpx.TimeoutException):
        raise NetworkError(
            f"Request timed out for {url}: {e}", error_code="NETWORK_TIMEOUT"
        ) from e
    elif isinstance(e, httpx.ConnectError):
        raise NetworkError(
            f"Connection error for {url}: {e}", error_code="CONNECTION_ERROR"
        ) from e
    elif isinstance(e, httpx.HTTPStatusError):
        raise HTTPError(
            f"HTTP error {e.response.status_code} for {url}",
            status_code=e.response.status_code,
            error_code=f"HTTP_{e.response.status_code}",
        ) from e
    else:
        raise NetworkError(
            f"Request error for {url}: {e}", error_code="REQUEST_ERROR"
        ) from e
