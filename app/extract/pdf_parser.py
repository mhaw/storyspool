import io

from PyPDF2 import PdfReader

from app.extract.errors import ParseError


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extracts text from PDF content.

    Args:
        pdf_content (bytes): The raw content of the PDF file.

    Returns:
        str: The extracted text from the PDF.

    Raises:
        ParseError: If text extraction from PDF fails.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        raise ParseError(
            f"Failed to extract text from PDF: {e}", error_code="PDF_PARSE_FAILED"
        )
