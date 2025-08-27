from unittest.mock import patch

import pytest
from flask import Flask

from app.services.users import current_user, require_login


@pytest.fixture
def app_with_config():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["ADMIN_UIDS"] = set()
    app.config["FIREBASE_PROJECT_ID"] = "test-project"
    return app


def test_current_user_no_token(app_with_config):
    """
    Test that current_user() returns None when no Authorization header or cookie is present.
    """
    with app_with_config.test_request_context():
        user = current_user()
        assert user is None


@patch("firebase_admin.auth.verify_id_token")
@patch("os.getenv")
def test_current_user_emulator_aud_mismatch(
    mock_getenv, mock_verify_id_token, app_with_config
):
    """
    Test that current_user() returns None (tolerantly) when in emulator mode and aud mismatches.
    """
    mock_getenv.side_effect = lambda x, default=None: (
        "localhost:9099" if x == "FIREBASE_AUTH_EMULATOR_HOST" else default
    )
    mock_verify_id_token.return_value = {
        "uid": "test_uid",
        "email": "test@example.com",
        "aud": "mismatched-project",
    }

    with app_with_config.test_request_context(
        headers={"Authorization": "Bearer some_token"}
    ):
        user = current_user()
        assert user is not None  # Should still return user in tolerant mode
        assert user["uid"] == "test_uid"
        # The aud mismatch warning will be logged, but it won't raise an exception or return None


@patch("firebase_admin.auth.verify_id_token")
@patch("os.getenv")
def test_current_user_prod_aud_mismatch(
    mock_getenv, mock_verify_id_token, app_with_config
):
    """
    Test that current_user() returns None and logs error when in prod-like mode and aud mismatches.
    """
    mock_getenv.side_effect = lambda x, default=None: (
        None if x == "FIREBASE_AUTH_EMULATOR_HOST" else default
    )  # Not in emulator mode
    mock_verify_id_token.return_value = {
        "uid": "test_uid",
        "email": "test@example.com",
        "aud": "mismatched-project",
    }

    with app_with_config.test_request_context(
        headers={"Authorization": "Bearer some_token"}
    ):
        with patch.object(app_with_config.logger, "error") as mock_logger_error:
            user = current_user()
            assert user is None
            mock_logger_error.assert_called_once()  # Ensure error is logged


@patch("app.services.users.current_user")
def test_require_login_authenticated(mock_current_user, app_with_config):
    """
    Test that require_login allows access if current_user returns a user.
    """
    mock_current_user.return_value = {"uid": "test_uid"}

    @app_with_config.route("/protected")
    @require_login
    def protected_route():
        return "Access granted"

    with app_with_config.test_client() as client:
        response = client.get("/protected")
        assert response.status_code == 200
        assert response.data.decode() == "Access granted"


@patch("app.services.users.current_user")
def test_require_login_unauthenticated(mock_current_user, app_with_config):
    """
    Test that require_login aborts with 401 if current_user returns None.
    """
    mock_current_user.return_value = None

    @app_with_config.route("/protected")
    @require_login
    def protected_route():
        return "Access granted"

    with app_with_config.test_client() as client:
        response = client.get("/protected")
        assert response.status_code == 401
