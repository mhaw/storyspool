from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import feedparser

# The Flask app is implicitly available via fixtures in conftest.py


def test_feed_integration(client):
    """
    Integration test for the RSS feed endpoint.
    - Mocks the data layer (`list_user_jobs`).
    - Makes a real request to the endpoint.
    - Parses the response with feedparser.
    - Validates the output.
    """
    # 1. Mock the data returned by the jobs service
    mock_user_id = "test-user-123"
    now = datetime.now(timezone.utc)
    mock_jobs_data = [
        {
            "job_id": "job-abc-123",
            "storage_path": "audio/job-abc-122.mp3",
            "article_title": "Test Article 1",
            "article_summary": "This is the summary for the first article.",
            "created_at": now - timedelta(days=1),
            "article_url": "http://example.com/article1",
            "audio_size_bytes": 1234567,
            "audio_duration_seconds": 185,
            "article_author": "Author One",
            "status": "COMPLETED",
        },
        {
            "job_id": "job-def-456",
            "storage_path": "audio/job-def-456.mp3",
            "article_title": "Test Article 2",
            "article_summary": "Summary for the second test article.",
            "created_at": now - timedelta(days=2),
            "article_url": "http://example.com/article2",
            "audio_size_bytes": 2345678,
            "audio_duration_seconds": 240,
            "article_author": "Author Two",
            "status": "COMPLETED",
        },
        {
            # This job should be ignored as it's not completed
            "job_id": "job-ghi-789",
            "status": "QUEUED",
        },
    ]

    # 2. Use patch to replace `list_user_jobs` during this test
    with patch(
        "app.services.rss.list_user_jobs", return_value=mock_jobs_data
    ) as mock_list_jobs:
        # 3. Make the HTTP request to the feed endpoint
        response = client.get(f"/u/{mock_user_id}/feed.xml")

        # 4. Assertions on the HTTP response
        assert response.status_code == 200
        assert "application/rss+xml" in response.content_type
        assert "max-age=300" in response.headers["Cache-Control"]

        # 5. Parse the XML content
        # We need to parse from the response data, not a URL
        feed = feedparser.parse(response.data)

        # 6. Assertions on the parsed feed content
        assert not feed.bozo, "Feed should be well-formed XML"
        assert feed.feed.title == "StorySpool Feed for test-user-123"
        assert len(feed.entries) == 2, "Should only include COMPLETED jobs"

        # Check entries (they are sorted newest first)
        entry1 = feed.entries[0]
        assert entry1.title == "Test Article 1"
        assert entry1.guid == "job-abc-123"
        assert entry1.summary == "This is the summary for the first article."
        assert entry1.author == "Author One"
        assert entry1.itunes_duration == "185"

        # Check enclosure details for the first entry
        assert len(entry1.enclosures) == 1
        enclosure1 = entry1.enclosures[0]
        assert "audio/job-abc-122.mp3" in enclosure1.href
        assert enclosure1.type == "audio/mpeg"
        assert enclosure1.length == "1234567"

        entry2 = feed.entries[1]
        assert entry2.title == "Test Article 2"
        assert entry2.guid == "job-def-456"

        # Ensure the mock was called correctly
        mock_list_jobs.assert_called_once_with(
            mock_user_id, limit=100, status="COMPLETED"
        )
