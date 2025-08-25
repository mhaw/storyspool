from flask import Flask, request
from .config import load_config
from .extensions import init_extensions
from .routes import bp as main_bp

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    load_config(app)
    init_extensions(app)

    # Blueprints
    app.register_blueprint(main_bp)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app
