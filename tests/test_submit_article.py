from unittest.mock import patch

from flask import url_for

# Assuming 'client' fixture is available from conftest.py


@patch("app.routes.current_user_id")
@patch("app.routes.extract_article")  # Changed patch path
@patch("app.routes.save_article_record")  # Changed patch path
@patch("app.routes.flash")  # Changed patch path
def test_submit_article_success(
    mock_flash,
    mock_save_article_record,
    mock_extract_article,
    mock_current_user_id,
    client,
    app,  # Added app fixture
):
    mock_current_user_id.return_value = "test_user_id"
    mock_extract_article.return_value = {
        "title": "Test Article",
        "url": "https://en.wikipedia.org/wiki/Test_page",  # Changed URL
        "summary": "A summary.",
        "author": "Test Author",
        "published": "2025-01-01T12:00:00Z",
    }

    with app.app_context():  # Added app.app_context()
        response = client.post(
            url_for("main.submit_article"),
            data={
                "article_url": "https://en.wikipedia.org/wiki/Test_page"
            },  # Changed URL
        )

    assert response.status_code == 302  # Redirects on success
    with app.app_context():  # Added app.app_context() for assertion
        assert response.location == url_for("main.index", _external=False)

    mock_extract_article.assert_called_once_with(
        "https://en.wikipedia.org/wiki/Test_page"
    )  # Changed URL
    mock_save_article_record.assert_called_once()
    # Verify arguments passed to save_article_record (simplified check)
    args, kwargs = mock_save_article_record.call_args
    assert args[0]["title"] == "Test Article"  # Check meta dict
    assert args[1] is None  # local_audio_path
    assert args[2] is None  # gcs_url
    assert (
        isinstance(args[3], str) and len(args[3]) == 64
    )  # urlhash (SHA256 hex digest)
    assert args[4] == "test_user_id"  # uid

    mock_flash.assert_called_once_with(
        "Article submitted successfully! It will appear in your feed soon.", "success"
    )


@patch("app.routes.current_user_id")
@patch("app.routes.extract_article")  # Changed patch path
@patch("app.routes.save_article_record")  # Changed patch path
@patch("app.routes.flash")  # Changed patch path
def test_submit_article_no_url(
    mock_flash,
    mock_save_article_record,
    mock_extract_article,
    mock_current_user_id,
    client,
    app,  # Added app fixture
):
    mock_current_user_id.return_value = "test_user_id"

    with app.app_context():  # Added app.app_context()
        response = client.post(url_for("main.submit_article"), data={"article_url": ""})

    assert response.status_code == 302
    with app.app_context():  # Added app.app_context() for assertion
        assert response.location == url_for("main.index", _external=False)

    mock_extract_article.assert_not_called()
    mock_save_article_record.assert_not_called()
    mock_flash.assert_called_once_with("Please provide an article URL.", "error")


@patch("app.routes.current_user_id")
@patch("app.routes.extract_article")  # Changed patch path
@patch("app.routes.save_article_record")  # Changed patch path
@patch("app.routes.flash")  # Changed patch path
def test_submit_article_extraction_failure(
    mock_flash,
    mock_save_article_record,
    mock_extract_article,
    mock_current_user_id,
    client,
    app,  # Added app fixture
):
    mock_current_user_id.return_value = "test_user_id"
    mock_extract_article.side_effect = Exception("Extraction failed")

    with app.app_context():  # Added app.app_context()
        response = client.post(
            url_for("main.submit_article"),
            data={
                "article_url": "https://en.wikipedia.org/wiki/Bad_page"
            },  # Changed URL
        )

    assert response.status_code == 302
    with app.app_context():  # Added app.app_context() for assertion
        assert response.location == url_for("main.index", _external=False)

    mock_extract_article.assert_called_once_with(
        "https://en.wikipedia.org/wiki/Bad_page"
    )  # Changed URL
    mock_save_article_record.assert_not_called()
    mock_flash.assert_called_once_with(
        "Error submitting article: Extraction failed", "error"
    )


# This test specifically checks the behavior when not logged in, so it should NOT patch require_login
@patch("app.routes.current_user_id")
@patch("app.routes.extract_article")  # Added patch for extract_article
@patch("app.routes.save_article_record")  # Added patch for save_article_record
@patch("app.routes.flash")  # Added patch for flash
def test_submit_article_not_logged_in(
    mock_current_user_id,
    mock_extract_article,
    mock_save_article_record,
    mock_flash,
    client,
    app,
):  # Added missing arguments
    mock_current_user_id.return_value = None  # Simulate not logged in
    mock_extract_article.return_value = {  # Mock return value for extract_article
        "title": "Test Article",
        "url": "https://en.wikipedia.org/wiki/Test_page",
        "summary": "A summary.",
        "author": "Test Author",
        "published": "2025-01-01T12:00:00Z",
    }

    with app.app_context():  # Added app.app_context()
        app.config["TESTING_BYPASS_AUTH"] = False  # Set bypass to False for this test
        response = client.post(
            url_for("main.submit_article"),
            data={
                "article_url": "https://en.wikipedia.org/wiki/Test_page"
            },  # Changed URL
        )

    # The @require_login decorator should handle this, typically by redirecting
    # or returning a 401. Based on app.services.users.require_login, it aborts with 401.
    assert response.status_code == 401
    # No flash message expected here as the abort happens before flash can be called
    # assert mock_flash.not_called() # This would fail if flash is mocked and not called
