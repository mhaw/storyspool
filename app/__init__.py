import logging

from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix

try:
    from flask_talisman import Talisman
except Exception:  # talisman optional in local
    Talisman = None
from .config import Config


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(Config)

    # Reverse-proxy aware headers (Cloud Run)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # Minimal CSP for Firebase + fonts (only in prod if Talisman available)
    if Talisman and app.config["APP_ENV"] == "prod":
        csp = {
            "default-src": ["'self'"],
            "style-src": ["'self'", "https://fonts.googleapis.com", "'unsafe-inline'"],
            "font-src": ["'self'", "https://fonts.gstatic.com", "data:"],
            "script-src": [
                "'self'",
                "https://www.gstatic.com",
                "https://www.googletagmanager.com",
                "https://apis.google.com",
            ],
            "connect-src": [
                "'self'",
                "https://firestore.googleapis.com",
                "https://www.googleapis.com",
                "https://securetoken.googleapis.com",
                "https://identitytoolkit.googleapis.com",
            ],
            "img-src": ["'self'", "data:"],
            "frame-src": ["'self'", "https://accounts.google.com"],
        }
        Talisman(
            app,
            content_security_policy=csp,
            force_https=(app.config["PREFERRED_URL_SCHEME"] == "https"),
        )

    # Expose Firebase Web config to templates
    @app.context_processor
    def inject_web_config():
        return {"FIREBASE_WEB_CONFIG": app.config["FIREBASE"]}

    # Add long cache headers for static in prod
    @app.after_request
    def add_cache_headers(resp):
        try:
            if app.config["APP_ENV"] == "prod" and request.path.startswith("/static/"):
                resp.headers["Cache-Control"] = (
                    f"public, max-age={app.config['SEND_FILE_MAX_AGE_DEFAULT']}"
                )
        except Exception:
            pass
        return resp

    # Boot log: resolved environment & public URL
    logging.getLogger().setLevel(logging.INFO)
    app.logger.info(
        {
            "event": "boot_config",
            "APP_ENV": app.config["APP_ENV"],
            "PUBLIC_BASE_URL": app.config.get("PUBLIC_BASE_URL"),
            "FIREBASE_projectId": app.config["FIREBASE"].get("projectId"),
        }
    )
    return app
