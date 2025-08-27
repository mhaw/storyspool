import datetime
import hashlib

import trafilatura
from flask import current_app  # New import

from app.extract.errors import (
    CanonicalizationError,
    ContentTypeError,
    HTTPError,
    NetworkError,
    ParseError,
)
from app.extract.fetch import fetch_content
from app.extract.models import ExtractedDocument
from app.extract.normalize import normalize_url
from app.extract.parse import detect_and_parse
from app.extract.pdf_parser import extract_text_from_pdf  # New import
from app.services.jobs import JobStatus  # New import


# Placeholder for persistence (will be implemented later)
async def persist_document(document: ExtractedDocument) -> None:
    """
    Placeholder function to persist the extracted document.
    In a real scenario, this would save to Firestore or another database.
    """
    print(
        f"[PERSIST] Document for {document.url_canonical} (ID: {document.id}) persisted."
    )
    # print(f"[PERSIST] Title: {document.title}")
    # print(f"[PERSIST] Text Excerpt: {document.text_excerpt[:100]}...")


# Placeholder for post-processing (will be implemented later)
def post_process_document(document_data: dict) -> dict:
    """
    Placeholder for post-processing extracted data.
    This could include text cleaning, truncation, entity recognition, etc.
    ""
    # For now, just truncate text_excerpt for storage
    text_excerpt = document_data.get("text", "")
    document_data["text_excerpt"] = text_excerpt[:500] if text_excerpt else None
    return document_data


async def extract_pipeline(url: str) -> ExtractedDocument:
    """
    Orchestrates the URL extraction pipeline.

    Args:
        url (str): The URL to extract content from.

    Returns:
        ExtractedDocument: The extracted and processed document.

    Raises:
        ExtractionError: If any stage of the pipeline fails.
    """
    canonical_url = None
    raw_content = None
    extracted_data = None
    status = "unknown"
    error_code = None
    parser_name = "N/A"
    parser_version = "N/A"

    try:
        # 1. Normalize URL
        canonical_url = normalize_url(url)
        doc_id = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()

        # 2. Fetch
        raw_content, metadata = await fetch_content(canonical_url)
        content_type = metadata.get("content_type", "")
        parser_name = "trafilatura"
        parser_version = trafilatura.__version__  # Get version dynamically

        # 3. Parse
        extracted_data = detect_and_parse(raw_content, canonical_url, content_type)

        # 4. Post-process
        processed_data = post_process_document(extracted_data)

        status = "success"

    except CanonicalizationError as e:
        status = "canonicalization_error"
        error_code = e.error_code or "CANONICALIZATION_FAILED"
        print(f"[ERROR] Canonicalization failed for {url}: {e}")
    except NetworkError as e:
        status = "fetch_error"
        error_code = e.error_code or "NETWORK_ERROR"
        print(f"[ERROR] Network error for {canonical_url or url}: {e}")
    except HTTPError as e:
        status = "fetch_error"
        error_code = e.error_code or f"HTTP_{e.status_code}"
        print(f"[ERROR] HTTP error for {canonical_url or url}: {e}")
    except ContentTypeError as e:
        status = "fetch_error"
        error_code = e.error_code or f"{JobStatus.FAILED_FETCH}_UNSUPPORTED_CONTENT_TYPE"
        print(f"[ERROR] Content type error for {canonical_url or url}: {e}")
    except ParseError as e:
        status = "parse_error"
        error_code = e.error_code or "PARSE_FAILED"
        print(f"[ERROR] Parse error for {canonical_url or url}: {e}")
    except Exception as e:
        status = "unhandled_error"
        error_code = "UNHANDLED_EXCEPTION"
        print(
            f"[ERROR] An unhandled exception occurred for {canonical_url or url}: {e}"
        )

    finally:
        # Ensure a document is always created, even on error, to record the attempt
        document = ExtractedDocument(
            id=(
                doc_id
                if "doc_id" in locals()
                else hashlib.sha256(url.encode("utf-8")).hexdigest()
            ),
            url_canonical=canonical_url or url,
            title=extracted_data.get("title") if extracted_data else None,
            text_excerpt=extracted_data.get("text_excerpt") if extracted_data else None,
            byline=extracted_data.get("author") if extracted_data else None,
            fetched_at=datetime.datetime.now(datetime.timezone.utc),
            parser_name=parser_name,
            parser_version=parser_version,
            status=status,
            error_code=error_code,
            raw_html_gcs_path=None,  # Not implemented yet
        )
        await persist_document(document)  # Persist the result (success or failure)
        return document