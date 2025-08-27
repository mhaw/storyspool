import pathlib
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.services.store import (
    _articles_col,
    list_user_articles,
    save_article_record,
    upload_audio_and_get_url,
)


def test_articles_col_initialization():
    """
    Test that _articles_col() returns a usable collection when FIRESTORE_DB is set.
    """
    app = Flask(__name__)
    # Mock a Firestore client
    mock_db_client = MagicMock()
    mock_collection = MagicMock()
    mock_db_client.collection.return_value = mock_collection

    with app.app_context():
        app.config["FIRESTORE_DB"] = mock_db_client
        app.config["FIRESTORE_COLLECTION"] = "test_articles"

        collection = _articles_col()
        assert collection is not None
        assert collection == mock_collection
        mock_db_client.collection.assert_called_with("test_articles")


def test_articles_col_no_firestore_db():
    """
    Test that _articles_col() raises RuntimeError if FIRESTORE_DB is not set.
    """
    app = Flask(__name__)
    with app.app_context():
        app.config["FIRESTORE_DB"] = None  # Explicitly set to None
        app.config["FIRESTORE_COLLECTION"] = (
            "test_articles"  # Still need this for the call
        )

        with pytest.raises(RuntimeError, match="Firestore client not initialized"):
            _articles_col()


def test_save_article_record():
    """Test that save_article_record correctly structures and saves a document."""
    # Arrange
    app = Flask(__name__)
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_document = MagicMock()
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document

    meta = {
        "title": "Test",
        "url": "http://test.com",
        "canonical_url": "http://test.com/canonical",
        "site": "test.com",
        "summary": "A summary",
        "author": "Author",
        "image": "img.jpg",
        "published": "2025-01-01",
    }
    local_audio_path = "/tmp/audio.mp3"
    gcs_url = "http://gcs.com/audio.mp3"
    urlhash = "testhash"
    uid = "user123"

    with app.app_context():
        app.config["FIRESTORE_DB"] = mock_db
        app.config["FIRESTORE_COLLECTION"] = "test_articles"

        # Act
        doc = save_article_record(meta, local_audio_path, gcs_url, urlhash, uid)

        # Assert
        mock_collection.document.assert_called_once_with(urlhash)
        mock_document.set.assert_called_once()
        assert doc["id"] == urlhash
        assert doc["title"] == "Test"


def test_list_user_articles():
    """Test listing articles for a specific user."""
    # Arrange
    app = Flask(__name__)
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value = (
        mock_query
    )

    # Mock the stream of documents
    mock_doc1 = MagicMock()
    mock_doc1.to_dict.return_value = {"title": "Article 1"}
    mock_doc2 = MagicMock()
    mock_doc2.to_dict.return_value = {"title": "Article 2"}
    mock_query.stream.return_value = [mock_doc1, mock_doc2]

    uid = "user123"

    with app.app_context():
        app.config["FIRESTORE_DB"] = mock_db
        app.config["FIRESTORE_COLLECTION"] = "test_articles"

        # Act
        articles = list_user_articles(uid)

        # Assert
        assert len(articles) == 2
        assert articles[0]["title"] == "Article 1"


@patch("app.services.store.gcs")
def test_upload_audio_and_get_url(mock_gcs):
    """Test uploading an audio file and getting a public URL."""
    # Arrange
    app = Flask(__name__)
    app.config["GCS_BUCKET"] = "test-bucket"

    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_gcs.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_blob.public_url = "http://gcs.com/public/audio.mp3"

    local_path = pathlib.Path("/tmp/test.mp3")
    filename = "test.mp3"

    with app.app_context():
        # Act
        url = upload_audio_and_get_url(local_path, filename)

        # Assert
        assert url == "http://gcs.com/public/audio.mp3"
        mock_bucket.blob.assert_called_once()
        mock_blob.upload_from_filename.assert_called_once_with(str(local_path))
        mock_blob.make_public.assert_called_once()
