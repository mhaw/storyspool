import os


class Config:
    APP_ENV = os.getenv("APP_ENV", "prod")
    # Cookie / scheme
    PREFERRED_URL_SCHEME = "https" if APP_ENV == "prod" else "http"
    SESSION_COOKIE_SECURE = APP_ENV == "prod"
    SESSION_COOKIE_SAMESITE = "Lax"
    # Static caching: prod long cache, local no cache
    SEND_FILE_MAX_AGE_DEFAULT = 31536000 if APP_ENV == "prod" else 0

    # Firebase Web SDK config injected into templates
    FIREBASE = {
        "apiKey": os.getenv("FIREBASE_API_KEY", ""),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "appId": os.getenv("FIREBASE_APP_ID", ""),
        "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", ""),
    }

    # Public base URL (optional; used for logging/self-check)
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")
