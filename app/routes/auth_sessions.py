import datetime

from firebase_admin import auth
from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    request,
)

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/sessionLogin", methods=["POST"])
def session_login():
    id_token = request.json.get("idToken")
    if not id_token:
        return (
            jsonify({"message": "Unauthorized", "error": "ID token not provided"}),
            401,
        )

    # Set session expiration to 5 days.
    expires_in = datetime.timedelta(days=5)
    try:
        # Create the session cookie. This will also verify the ID token.
        session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)
    except Exception as e:
        return jsonify({"message": "Unauthorized", "error": str(e)}), 401

    response = make_response(
        jsonify({"message": "Session cookie set successfully"}), 200
    )
    # Set the session cookie in the response.
    # httponly: True to prevent client-side JavaScript access.
    # secure: True to ensure the cookie is only sent over HTTPS.
    # samesite: 'Lax' or 'Strict' for CSRF protection.
    response.set_cookie(
        current_app.config["COOKIE_NAME"],
        session_cookie,
        max_age=int(expires_in.total_seconds()),
        httponly=True,
        secure=current_app.config["SESSION_COOKIE_SECURE"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
    )
    return response


@auth_bp.route("/sessionLogout", methods=["POST"])
def session_logout():
    response = make_response(jsonify({"message": "Session cookie cleared"}), 200)
    response.set_cookie(
        current_app.config["COOKIE_NAME"],
        "",
        max_age=0,  # Expire the cookie immediately
        httponly=True,
        secure=current_app.config["SESSION_COOKIE_SECURE"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
    )
    return response
