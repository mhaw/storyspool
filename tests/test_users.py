from unittest.mock import patch

import pytest
from flask import Flask

from app.services.users import (  # Removed current_user import
    current_user_id,
    require_login,
)


@pytest.fixture
def app_with_config():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["ADMIN_UIDS"] = set()
    app.config["FIREBASE_PROJECT_ID"] = "test-project"
    # Add TESTING_BYPASS_AUTH for current_user_id testing
    app.config["TESTING_BYPASS_AUTH"] = False  # Ensure it's false for these tests
    return app


def test_current_user_id_no_token(app_with_config):  # Renamed test
    """
    Test that current_user_id() returns None when no Authorization header is present.
    """
    with app_with_config.test_request_context():
        user_id = current_user_id()  # Changed to current_user_id
        assert user_id is None


@patch("firebase_admin.auth.verify_id_token")
@patch("os.getenv")
def test_current_user_id_emulator_aud_mismatch(  # Renamed test
    mock_getenv, mock_verify_id_token, app_with_config
):
    """
    Test that current_user_id() returns UID even with aud mismatch in emulator mode.
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
        user_id = current_user_id()  # Changed to current_user_id
        assert user_id == "test_uid"  # Should return UID in tolerant mode


@patch("firebase_admin.auth.verify_id_token")
@patch("os.getenv")
def test_current_user_id_prod_aud_mismatch(  # Renamed test
    mock_getenv, mock_verify_id_token, app_with_config
):
    """
    Test that current_user_id() returns None and logs error when in prod-like mode and aud mismatches.
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
        with patch.object(
            app_with_config.logger, "warning"
        ) as mock_logger_warning:  # Changed to warning
            user_id = current_user_id()  # Changed to current_user_id
            assert user_id is None
            mock_logger_warning.assert_called_once()  # Ensure warning is logged


@patch("app.services.users.current_user_id")  # Changed patch path
def test_require_login_authenticated(
    mock_current_user_id, app_with_config
):  # Changed argument name
    """
    Test that require_login allows access if current_user_id returns a user ID.
    """
    mock_current_user_id.return_value = "test_uid"  # Changed to test_uid

    @app_with_config.route("/protected")
    @require_login
    def protected_route():
        return "Access granted"

    with app_with_config.test_client() as client:
        response = client.get("/protected")
        assert response.status_code == 200
        assert response.data.decode() == "Access granted"


@patch("app.services.users.current_user_id")  # Changed patch path
def test_require_login_unauthenticated(
    mock_current_user_id, app_with_config
):  # Changed argument name
    """
    Test that require_login aborts with 401 if current_user_id returns None.
    """
    mock_current_user_id.return_value = None

    @app_with_config.route("/protected")
    @require_login
    def protected_route():
        return "Access granted"

    with app_with_config.test_client() as client:
        response = client.get("/protected")
        assert response.status_code == 401
