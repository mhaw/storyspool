"""
Firebase Admin SDK and Firestore client initialization helper.
Ensures the SDK is initialized once with the correct project ID and returns a Firestore client.
"""

import os

from firebase_admin import auth, credentials, firestore, initialize_app


def init_firebase_admin(app_config, app_logger):
    """
    Initializes the Firebase Admin SDK and returns a Firestore client.
    Uses FIREBASE_PROJECT_ID from app config and respects emulator hosts.
    """
    firebase_project_id = app_config.get("FIREBASE_PROJECT_ID")

    if not firebase_project_id:
        app_logger.warning(
            "FIREBASE_PROJECT_ID is not set in app config. Firebase Admin SDK will attempt default initialization."
        )
        # Fallback to default initialization if project ID is not explicitly set
        # This might pick up project ID from GOOGLE_APPLICATION_CREDENTIALS or GCLOUD_PROJECT
        initialize_app()
    else:
        # Explicitly initialize with the project ID from config
        # This is crucial for "aud" claim verification
        initialize_app(options={"projectId": firebase_project_id})
        app_logger.debug(
            f"Firebase Admin SDK initialized with project ID: {firebase_project_id}"
        )

    # Firestore client will automatically respect FIRESTORE_EMULATOR_HOST if set
    db = firestore.client()
    app_logger.debug("Firestore client initialized.")

    # Log emulator status for clarity
    auth_emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
    firestore_emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
    if auth_emulator_host or firestore_emulator_host:
        app_logger.info(
            f"Firebase Emulators active: Auth={auth_emulator_host}, Firestore={firestore_emulator_host}"
        )
    else:
        app_logger.info(
            "Firebase Emulators not active. Connecting to production Firebase."
        )

    return db
