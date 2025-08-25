import functools
from functools import lru_cache

from firebase_admin import auth, initialize_app
from flask import abort, g, request

_inited = False


def _ensure_init():
    global _inited
    if not _inited:
        initialize_app()
        _inited = True


def _bearer_token():
    hdr = request.headers.get("Authorization", "")
    if hdr.lower().startswith("bearer "):
        return hdr.split(" ", 1)[1].strip()
    return request.cookies.get("id_token")


def current_user():
    _ensure_init()
    tok = _bearer_token()
    if not tok:
        return None
    try:
        decoded = auth.verify_id_token(tok, check_revoked=False)
        uid = decoded.get("uid")
        email = decoded.get("email")
        from flask import current_app

        is_admin = uid in current_app.config["ADMIN_UIDS"]
        return {"uid": uid, "email": email, "is_admin": is_admin}
    except Exception:
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
            abort(401)
        g.user = u
        return fn(*args, **kwargs)

    return wrapper
