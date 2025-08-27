import functools
import os  # New import

from firebase_admin import auth
from flask import abort, current_app, g, request  # Import current_app


def _bearer_token():
    hdr = request.headers.get("Authorization", "")
    if hdr.lower().startswith("bearer "):
        token = hdr.split(" ", 1)[1].strip()
        current_app.logger.debug(
            f"Found Bearer token in Authorization header: {token[:10]}..."
        )  # Log first 10 chars
        return token
    token = request.cookies.get("id_token")
    if token:
        current_app.logger.debug(
            f"Found id_token in cookie: {token[:10]}..."
        )  # Log first 10 chars
    else:
        current_app.logger.debug("No token found in Authorization header or cookie.")
    return token


def current_user():
    tok = _bearer_token()
    if not tok:
        current_app.logger.debug("current_user: No token provided, returning None.")
        return None
    try:
        decoded = auth.verify_id_token(tok, check_revoked=False)
        uid = decoded.get("uid")
        email = decoded.get("email")

        # Check audience claim if not in emulator mode
        firebase_project_id = current_app.config.get("FIREBASE_PROJECT_ID")
        auth_emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")

        if firebase_project_id and decoded.get("aud") != firebase_project_id:
            if not auth_emulator_host:  # Not in emulator mode, so strict check
                current_app.logger.error(
                    f"Token verification failed: Incorrect 'aud' claim. Expected '{firebase_project_id}' but got '{decoded.get('aud')}'."
                )
                return None
            else:  # In emulator mode, be tolerant
                current_app.logger.warning(
                    f"Token 'aud' mismatch in emulator mode. Expected '{firebase_project_id}' but got '{decoded.get('aud')}'. Proceeding with caution."
                )

        current_app.logger.debug(f"Token verified for UID: {uid}, Email: {email}")
        is_admin = uid in current_app.config["ADMIN_UIDS"]
        return {"uid": uid, "email": email, "is_admin": is_admin}
    except Exception as e:
        # Log failures as one-liners, no stack unless debug is enabled.
        log_level = (
            current_app.logger.debug
            if current_app.debug
            else current_app.logger.error
        )
        log_level(f"Token verification failed: {e}")
        return None


def current_user_id():
    u = current_user()
    return u["uid"] if u else None


def user_display_name(uid: str) -> str:
    return f"User-{uid[:6]}"


def require_login(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            current_app.logger.warning(
                "require_login: User not authenticated, aborting 401."
            )
            abort(401)
        g.user = u
        return fn(*args, **kwargs)

    return wrapper
gs)

    return wrapper
