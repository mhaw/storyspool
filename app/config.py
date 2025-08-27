import os
import sys

REQUIRED_ENVS = [
    "GCP_PROJECT",
    "GCS_BUCKET",
    "FIRESTORE_COLLECTION",
    "BASE_URL",
    "FIREBASE_PROJECT_ID",
    "TASK_TOKEN",
]


def _validate_config(app):
    missing_envs = []
    for env_var in REQUIRED_ENVS:
        if not app.config.get(env_var):
            missing_envs.append(env_var)

    if missing_envs:
        app.logger.error(
            f"Missing or empty required environment variables: {', '.join(missing_envs)}. "
            "Please set them before running the application."
        )
        sys.exit(1)  # Exit application if critical configs are missing


def load_config(app):
    # Flask
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    # Project identity
    app.config["APP_NAME"] = "StorySpool"
    # GCP
    app.config["GCP_PROJECT"] = os.getenv("GCP_PROJECT", "")
    app.config["GCS_BUCKET"] = os.getenv("GCS_BUCKET", "")
    app.config["FIRESTORE_COLLECTION"] = os.getenv("FIRESTORE_COLLECTION", "articles")
    # TTS
    app.config["TTS_VOICE"] = os.getenv("TTS_VOICE", "en-US-Neural2-C")
    app.config["TTS_SPEAKING_RATE"] = float(os.getenv("TTS_SPEAKING_RATE", "1.0"))
    app.config["TTS_PITCH"] = float(os.getenv("TTS_PITCH", "0.0"))
    # Base URL
    app.config["BASE_URL"] = os.getenv("BASE_URL", "http://localhost:8080")
    # Firebase/Auth
    app.config["FIREBASE_PROJECT_ID"] = os.getenv("FIREBASE_PROJECT_ID", "")
    app.config["ADMIN_UIDS"] = set(
        uid.strip() for uid in os.getenv("ADMIN_UIDS", "").split(",") if uid.strip()
    )
    # Queue
    app.config["TASKS_QUEUE"] = os.getenv("TASKS_QUEUE", "speakaudio2-jobs")
    app.config["TASKS_LOCATION"] = os.getenv("TASKS_LOCATION", "us-central1")
    app.config["TASK_TOKEN"] = os.getenv("TASK_TOKEN", "")
    # Logging
    app.config["DEV_PRETTY_LOGS"] = (
        os.getenv("DEV_PRETTY_LOGS", "true").lower() == "true"
    )
    app.config["USE_STRUCTURED_LOGGING"] = (
        os.getenv("USE_STRUCTURED_LOGGING", "false").lower() == "true"
    )

    _validate_config(app)
