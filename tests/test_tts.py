from unittest.mock import MagicMock, patch

import pytest

from app.services.tts import chunk_text, synthesize_article_to_mp3


@pytest.fixture
def mock_app_context():
    """Fixture to provide a mock Flask app context for logging."""
    app = MagicMock()
    app.logger = MagicMock()
    with patch("app.services.tts.current_app", app):
        yield app


@patch("app.services.tts.texttospeech.TextToSpeechClient")
@patch("app.services.tts.AudioSegment")
@patch("app.services.tts.upload_audio_and_get_url")
@patch("app.services.tts.tempfile.mkdtemp")
@patch("app.services.tts.pathlib.Path")
def test_synthesize_article_to_mp3_success(
    mock_path,
    mock_mkdtemp,
    mock_upload,
    mock_audio_segment,
    mock_tts_client,
    mock_app_context,
):
    """Test the successful synthesis of an article to MP3."""
    # Arrange
    meta = {"text": "This is a short text."}
    urlhash = "test_hash"

    mock_tts_instance = mock_tts_client.return_value
    mock_tts_instance.synthesize_speech.return_value.audio_content = b"mp3_data"

    # Mock AudioSegment methods
    mock_segment_instance = MagicMock()
    mock_audio_segment.empty.return_value = mock_segment_instance
    mock_audio_segment.from_mp3.return_value = mock_segment_instance
    mock_segment_instance.__iadd__.return_value = mock_segment_instance  # Handle +=

    mock_upload.return_value = "http://gcs.com/audio.mp3"

    # Act
    local_path, gcs_url = synthesize_article_to_mp3(meta, urlhash)

    # Assert
    assert gcs_url == "http://gcs.com/audio.mp3"
    mock_tts_client.assert_called_once()
    mock_tts_instance.synthesize_speech.assert_called_once()
    mock_audio_segment.empty.assert_called_once()
    mock_audio_segment.from_mp3.assert_called_once()
    mock_upload.assert_called_once()
    mock_segment_instance.export.assert_called_once()


def test_chunk_text():
    """Test the text chunking logic."""
    long_text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    chunks = chunk_text(long_text, max_len=20)
    assert len(chunks) == 3
    assert chunks[0] == "Paragraph one."
    assert chunks[1] == "Paragraph two."
    assert chunks[2] == "Paragraph three."
