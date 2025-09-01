import functools

from firebase_admin import auth
from flask import abort, current_app, g, make_response, redirect, request, url_for


def current_user_id():
    """Returns the current user's UID from Firebase Auth, or None."""
    if hasattr(g, "user") and g.user:
        return g.user["uid"]
    return None


def require_login(f):
    """Decorator to require a user to be logged in."""

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get("TESTING_BYPASS_AUTH"):  # Bypass auth for testing
            g.user = {"uid": "test_user_id"}  # Set a dummy user for testing
            return f(*args, **kwargs)

        # 1. Check for Firebase session cookie
        session_cookie = request.cookies.get(current_app.config["COOKIE_NAME"])
        if session_cookie:
            try:
                decoded_token = auth.verify_session_cookie(
                    session_cookie, check_revoked=True
                )
                g.user = decoded_token
                current_app.logger.info(
                    f"User {g.user['uid']} authenticated via session cookie."
                )
                return f(*args, **kwargs)
            except Exception as e:
                current_app.logger.warning(f"Session cookie verification failed: {e}")
                # If session cookie is invalid, clear it and redirect
                response = make_response(redirect(url_for("main.index")))
                response.set_cookie(
                    current_app.config["COOKIE_NAME"],
                    "",
                    max_age=0,
                    httponly=True,
                    secure=current_app.config["SESSION_COOKIE_SECURE"],
                    samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
                )
                return response
        else:
            current_app.logger.info(
                "No valid session cookie found. Attempting ID token authentication."
            )

        # 2. Fallback: Check for Firebase ID token in the Authorization header (for API calls)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            id_token = auth_header.split("Bearer ")[1]
            try:
                decoded_token = auth.verify_id_token(id_token)
                g.user = decoded_token
                current_app.logger.info(
                    f"User {g.user['uid']} authenticated via ID token."
                )
                return f(*args, **kwargs)
            except Exception as e:
                current_app.logger.warning(f"ID token verification failed: {e}")
                abort(401)  # Unauthorized

        # If neither session cookie nor ID token is valid
        current_app.logger.warning(
            "require_login: User not authenticated, aborting 401 or redirecting."
        )
        if (
            request.accept_mimetypes.accept_html
            and not request.accept_mimetypes.accept_json
        ):
            return redirect(url_for("main.index"))  # Redirect to login page
        else:
            abort(401)  # Unauthorized

    return decorated_function
