import os

import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    # Prefer ADC on Cloud Run; fall back to explicit creds if provided
    if not firebase_admin._apps:
        cred = None
        # If running locally with a JSON key, allow it—but don't require it on Cloud Run
        key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if key_path and os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
        else:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(
            cred,
            {
                "projectId": os.getenv("FIREBASE_PROJECT_ID")
                or os.getenv("GOOGLE_CLOUD_PROJECT")
            },
        )
    return firestore.client()


db = init_firebase()
