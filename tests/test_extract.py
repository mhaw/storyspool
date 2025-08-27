import json
from unittest.mock import patch

from flask import Flask

from app.services.extract import extract_article


@patch("app.services.extract.trafilatura.fetch_url")
@patch("app.services.extract.trafilatura.extract")
def test_extract_article_success(mock_extract, mock_fetch_url):
    """Test the successful extraction of an article using trafilatura."""
    # Arrange
    url = "http://example.com/article"
    mock_fetch_url.return_value = "<html><body><h1>Title</h1><p>Text</p></body></html>"
    mock_extract.return_value = json.dumps(
        {
            "title": "Test Title",
            "author": "Test Author",
            "text": "This is the article text.",
            "image": "http://example.com/image.jpg",
            "date": "2025-08-25",
            "source": "http://example.com/canonical",
            "language": "en",
        }
    )

    app = Flask(__name__)
    with app.app_context():
        # Act
        result = extract_article(url)

        # Assert
        assert result["title"] == "Test Title"
        assert result["author"] == "Test Author"
        assert result["text"] == "This is the article text."
        assert result["url"] == url
        assert result["site"] == "example.com"
        mock_fetch_url.assert_called_once_with(url)
        mock_extract.assert_called_once()


@patch("app.services.extract.requests.get")
@patch("app.services.extract.trafilatura.fetch_url")
@patch("app.services.extract.trafilatura.extract")
def test_extract_article_fallback(mock_extract, mock_fetch_url, mock_requests_get):
    """Test the fallback extraction logic when trafilatura fails."""
    # Arrange
    url = "http://example.com/fallback"
    sample_html = """
    <html>
        <head><title>Fallback Title</title></head>
        <body><p>Fallback text.</p></body>
    </html>
    """
    mock_fetch_url.return_value = (
        "<html>...</html>"  # This is for the first extract call
    )
    # Simulate trafilatura returning no data on the first call, then fallback text on the second
    mock_extract.side_effect = [
        "{}",  # First call returns empty JSON
        "Fallback text.",  # Second call inside the fallback logic returns the text
    ]

    mock_response = mock_requests_get.return_value
    mock_response.text = sample_html
    mock_response.raise_for_status.return_value = None

    app = Flask(__name__)
    with app.app_context():
        # Act
        result = extract_article(url)

        # Assert
        assert result["title"] == "Fallback Title"
        assert "Fallback text." in result["text"]
        mock_requests_get.assert_called_once()
