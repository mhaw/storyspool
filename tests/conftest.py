import os
import sys
from unittest.mock import MagicMock

import pytest

# Mock external dependencies at the very top level to ensure they are mocked
# before any application code is imported during test collection.
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.auth"] = MagicMock()
sys.modules["pydub"] = MagicMock()
sys.modules["pydub.AudioSegment"] = MagicMock()


# This import now happens after mocks are in place
from app import create_app

# Add the project root to the Python path to allow tests to import the 'app' module.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(scope="session")
def app():
    """
    Create and configure a new app instance for each test.
    """
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "GCS_BUCKET_NAME": "test-bucket",
            "SERVER_NAME": "localhost",
            "TESTING_BYPASS_AUTH": True,
            "SECRET_KEY": "test_secret_key",
            "FIRESTORE_DB": MagicMock(),
            "FIRESTORE_COLLECTION": "test_collection",  # Added FIRESTORE_COLLECTION
            # You can override other config settings here for tests
            # For example, using a different database or disabling services.
            # e.g., "GCS_BUCKET_NAME": "fake-test-bucket"
        }
    )
    yield app


@pytest.fixture(scope="session")
def client(app):
    """
    A test client for the app."""
    return app.test_client()
