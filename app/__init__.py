import datetime  # Import datetime
import logging
from urllib.parse import urlparse  # Import urlparse

from flask import Flask
from pythonjsonlogger import jsonlogger

from .config import load_config
from .extensions import init_extensions
from .firebase_admin_ext import init_firebase_admin  # New import
from .routes import bp as main_bp

# Removed: from firebase_admin import initialize_app # Moved to firebase_admin_ext


def urlparse_filter(value):
    """Jinja2 filter to parse URLs."""
    return urlparse(value)


def timeago_filter(dt):
    """Jinja2 filter to format datetime as 'time ago'."""
    now = datetime.datetime.now(datetime.timezone.utc)  # Ensure timezone awareness
    if dt.tzinfo is None:  # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    diff = now - dt

    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} minutes ago"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hours ago"
    days = hours / 24
    if days < 30:
        return f"{int(days)} days ago"
    months = days / 30
    if months < 12:
        return f"{int(months)} months ago"
    years = days / 365
    return f"{int(years)} years ago" ""


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    load_config(app)

    # Set logging level to DEBUG for development
    app.logger.setLevel(logging.DEBUG)

    # Configure JSON logging for production
    if app.config.get("USE_STRUCTURED_LOGGING"):
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            "%(levelname)s %(asctime)s %(filename)s %(lineno)d %(message)s"
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.info("Using structured JSON logging.")
    else:
        # Default Flask logger is already configured for console output
        app.logger.info("Using basic console logging.")

    # Initialize Firebase Admin SDK and Firestore client
    # This will also log the resolved FIREBASE_PROJECT_ID and emulator status
    app.config["FIRESTORE_DB"] = init_firebase_admin(app.config, app.logger)

    init_extensions(app)

    # Register custom Jinja2 filters
    app.jinja_env.filters["urlparse"] = urlparse_filter
    app.jinja_env.filters["timeago"] = timeago_filter  # Register timeago filter

    @app.context_processor
    def inject_global_vars():
        return dict(cache_buster=datetime.datetime.now().timestamp())

    # Blueprints
    app.register_blueprint(main_bp)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    @app.after_request
    def add_security_headers(response):
        response.headers["Cross-Origin-Opener-Policy"] = "unsafe-none"
        return response

    return app
