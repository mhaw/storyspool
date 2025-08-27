import trafilatura

from app.extract.errors import ParseError


def detect_and_parse(raw_content: bytes, url: str, content_type: str) -> dict:
    """
    Detects content type and parses raw content into structured data using Trafilatura.

    Args:
        raw_content (bytes): The raw content (HTML) to parse.
        url (str): The URL from which the content was fetched (for Trafilatura context).
        content_type (str): The content type of the raw content.

    Returns:
        dict: A dictionary containing extracted data like 'text', 'title', 'author', etc.

    Raises:
        ParseError: If parsing fails or yields no meaningful data.
    """
    if "text/html" not in content_type:
        raise ParseError(
            f"Unsupported content type for parsing: {content_type}. Expected text/html.",
            error_code="UNSUPPORTED_CONTENT_TYPE_PARSE",
        )

    # Use trafilatura to extract main content
    # Set include_comments=False to avoid pulling in comments as part of the text
    # Set no_fallback=True to prevent trafilatura from trying other methods if initial fails
    extracted_data = trafilatura.extract(
        raw_content,
        url=url,
        include_comments=False,
        no_fallback=False,  # Allow trafilatura's internal fallbacks
        output_format="json",  # Request JSON output for easier parsing
        with_metadata=True,
    )

    if not extracted_data:
        raise ParseError(
            f"Trafilatura failed to extract any meaningful content from {url}",
            error_code="NO_CONTENT_EXTRACTED",
        )

    # trafilatura.extract with output_format='json' returns a JSON string
    # We need to parse it back into a Python dict
    import json

    try:
        parsed_json = json.loads(extracted_data)
    except json.JSONDecodeError as e:
        raise ParseError(
            f"Failed to decode JSON from Trafilatura output for {url}: {e}",
            error_code="TRAFILATURA_JSON_DECODE_ERROR",
        )

    # Basic validation of extracted data
    if not parsed_json.get("text") and not parsed_json.get("title"):
        raise ParseError(
            f"Extracted content from {url} is empty or lacks title/text.",
            error_code="EMPTY_EXTRACTED_CONTENT",
        )

    return parsed_json
