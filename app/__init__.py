import logging

from flask import Flask

from .config import load_config
from .extensions import init_extensions
from .firebase_admin_ext import init_firebase_admin  # New import
from .routes import bp as main_bp

# Removed: from firebase_admin import initialize_app # Moved to firebase_admin_ext



def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    load_config(app)

    # Set logging level to DEBUG for development
    app.logger.setLevel(logging.DEBUG)

    # Initialize Firebase Admin SDK and Firestore client
    # This will also log the resolved FIREBASE_PROJECT_ID and emulator status
        app.config["FIRESTORE_DB"] = init_firebase_admin(
        app.config, app.logger
    )

    init_extensions(app)

    # Blueprints
    app.register_blueprint(main_bp)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app
