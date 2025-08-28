from unittest.mock import MagicMock, patch

import pytest

from app.worker import run_job


@pytest.fixture
def mock_app_context():
    """Fixture to provide a mock Flask app context."""
    # The app context is needed for logging and config access in the worker.
    app = MagicMock()
    app.logger = MagicMock()
    app.config = {}
    with patch("app.worker.current_app", app):
        yield app


@patch("app.worker.get_job")
@patch("app.worker.update_job")
@patch("app.worker.extract_article")
@patch("app.worker.synthesize_article_to_mp3")
@patch("app.worker.save_article_record")
def test_run_job_success(
    mock_save_article,
    mock_synthesize,
    mock_extract,
    mock_update_job,
    mock_get_job,
    mock_app_context,
):
    """Test the successful execution path of run_job."""
    # Arrange: Set up the mock return values
    job_id = "test_job_123"
    mock_get_job.return_value = {
        "id": job_id,
        "url": "http://example.com/article",
        "urlhash": "somehash",
        "user_id": "user123",
        "status": "queued",
    }
    mock_extract.return_value = {"title": "Test Title", "text": "Some text."}
    mock_synthesize.return_value = (
        "local/path/to/audio.mp3",
        "http://gcs.com/audio.mp3",
    )
    mock_save_article.return_value = {
        "title": "Test Title"
    }  # Match what update_job needs

    # Act: Run the job
    success, message = run_job(job_id)

    # Assert: Verify the outcome and the sequence of calls
    assert success is True
    assert message == "ok"

    # Check that the job status was updated correctly
    assert mock_update_job.call_count == 5
    mock_update_job.assert_any_call(job_id, status="fetching")
    mock_update_job.assert_any_call(job_id, status="parsing", title="Test Title")
    mock_update_job.assert_any_call(job_id, status="tts_generating")
    mock_update_job.assert_any_call(job_id, status="uploading_audio")
    mock_update_job.assert_any_call(
        job_id,
        status="done",
        audio_url="http://gcs.com/audio.mp3",
        title="Test Title",
        processing_duration_seconds=0,  # processing_duration_seconds is added by run_job
    )

    # Verify that all the services were called
    mock_extract.assert_called_once_with("http://example.com/article")
    mock_synthesize.assert_called_once()
    mock_save_article.assert_called_once()


@patch("app.worker.get_job")
@patch("app.worker.update_job")
@patch("app.worker.extract_article")
def test_run_job_failure(mock_extract, mock_update_job, mock_get_job, mock_app_context):
    """Test the failure path of run_job."""
    # Arrange: Set up mocks for a failure scenario
    job_id = "test_job_fail"
    # Simulate the job status being 'fetching' when the error occurs
    mock_get_job.side_effect = [
        {
            "id": job_id,
            "url": "http://example.com/broken-article",
            "status": "queued",
        },
        {"status": "fetching"},  # Mock the status check inside the except block
    ]
    # Simulate the extraction failing
    exception_message = "Extraction failed miserably"
    mock_extract.side_effect = Exception(exception_message)

    # Act: Run the job
    success, message = run_job(job_id)

    # Assert: Verify the failure outcome
    assert success is False
    assert message == exception_message

    # Check that the job status was updated to fetching, then to the correct failed status
    assert mock_update_job.call_count == 2
    mock_update_job.assert_any_call(job_id, status="fetching")
    mock_update_job.assert_any_call(
        job_id,
        status="failed_fetch",
        last_error="We couldn't process this URL. It might be a paywalled article, a video, or a page without a clear body of text. Please try a different URL.",
    )
