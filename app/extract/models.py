import dataclasses
import datetime


@dataclasses.dataclass
class ExtractedDocument:
    """
    Represents a document extracted from a URL.

    Attributes:
        id (str): SHA256 hash of url_canonical, serving as the unique identifier.
        url_canonical (str): The canonical URL of the extracted content.
        fetched_at (datetime.datetime): Timestamp when the content was successfully fetched.
        parser_name (str): The name of the parser used (e.g., "trafilatura", "playwright").
        parser_version (str): The version of the parser library used.
        status (str): The status of the extraction ("success", "fetch_error", "parse_error").
        title (str | None): The title of the extracted content.
        text_excerpt (str | None): A truncated excerpt of the readable text.
        byline (str | None): The author or byline of the content.
        error_code (str | None): A specific error code if an error occurred.
        raw_html_gcs_path (str | None): Optional GCS path to the stored raw HTML.
    """

    id: str
    url_canonical: str
    fetched_at: datetime.datetime
    parser_name: str
    parser_version: str
    status: str
    title: str | None = None
    text_excerpt: str | None = None
    byline: str | None = None
    error_code: str | None = None
    raw_html_gcs_path: str | None = None
