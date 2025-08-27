from unittest.mock import MagicMock

import pytest
from flask import Flask

from app.services.jobs import create_job


@pytest.fixture
def mock_db():
    """Fixture to provide a mock Firestore client."""
    db = MagicMock()
    db.collection.return_value.document.return_value.get.return_value.exists = False
    return db


def test_create_job_new(mock_db):
    """Test creating a new job."""
    # Arrange
    app = Flask(__name__)
    app.config["FIRESTORE_DB"] = mock_db
    url = "http://example.com/new-job"
    uid = "user123"

    with app.app_context():
        # Act
        job = create_job(url, uid)

        # Assert
        assert job["status"] == "queued"
        assert job["url"] == url
        assert job["user_id"] == uid
        mock_db.collection.return_value.document.return_value.set.assert_called_once()


def test_create_job_existing(mock_db):
    """Test creating a job that already exists."""
    # Arrange
    app = Flask(__name__)
    app.config["FIRESTORE_DB"] = mock_db
    url = "http://example.com/existing-job"
    uid = "user456"
    existing_doc = {"id": "some_hash", "status": "done"}
    mock_db.collection.return_value.document.return_value.get.return_value.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value.to_dict.return_value = (
        existing_doc
    )

    with app.app_context():
        # Act
        job = create_job(url, uid)

        # Assert
        assert job == existing_doc
        mock_db.collection.return_value.document.return_value.set.assert_not_called()
