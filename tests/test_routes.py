import pytest
from unittest.mock import MagicMock, patch

from flask import url_for


@pytest.fixture
def client(app):
    app.config.update(
        {
            "TESTING": True,
            # Mock Firebase and other external services
            "FIRESTORE_DB": MagicMock(),
            "FIREBASE_APP": MagicMock(),
        }
    )
    with app.test_client() as client:
        with app.app_context():
            yield client


@patch("app.routes.current_user_id")
def test_index_anonymous(mock_current_user_id, client):
    """Test the index page for an anonymous user."""
    mock_current_user_id.return_value = None
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sign In / Get Started" in response.data


@patch("app.routes.current_user_id")
def test_index_authenticated(mock_current_user_id, client):
    """Test the index page for an authenticated user, should redirect."""
    mock_current_user_id.return_value = "user123"
    response = client.get("/")
    assert response.status_code == 302
    assert response.location == url_for("main.article_list", _external=False)


@patch("app.services.users.current_user")
@patch("app.routes.list_user_jobs")
@patch("app.routes.url_for")
def test_article_list_authenticated(
    mock_url_for, mock_list_user_jobs, mock_current_user, client
):
    """Test the article list page for an authenticated user."""
    mock_current_user.return_value = {"uid": "user123"}
    mock_list_user_jobs.return_value = []
    mock_url_for.return_value = "http://example.com/feed.xml"

    response = client.get("/articles")
    assert response.status_code == 200
    assert b"My Articles" in response.data
    assert b"Get My Podcast Feed" in response.data


@patch("app.routes.current_user_id")
def test_article_list_anonymous(mock_current_user_id, client):
    """Test that the article list page requires login."""
    mock_current_user_id.return_value = None
    response = client.get("/articles")
    # The require_login decorator should redirect to the home page
    assert response.status_code == 401
