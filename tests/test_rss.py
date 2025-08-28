from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import pytest

from app.services import rss

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"


@pytest.fixture
def sample_items():
    return [
        {
            "guid": "test-guid-123",
            "title": "Test Article 1",
            "summary": "This is a summary of the first article.",
            "pub_date": datetime(2025, 8, 28, 10, 0, 0, tzinfo=timezone.utc),
            "source_url": "http://example.com/article1",
            "enclosure_url": "http://example.com/audio/article1.mp3",
            "enclosure_length": 12345678,
            "duration": 300,
            "author": "Author One",
        }
    ]


@pytest.fixture
def sample_channel():
    return {
        "title": "Test User's Feed",
        "link": "http://example.com/user/test-user",
        "description": "A test feed for a user.",
        "author": "Test Author",
        "owner_name": "Test Owner",
        "owner_email": "test@example.com",
        "image_url": "http://example.com/image.png",
    }


def test_build_feed_structure_and_tags(sample_channel, sample_items):
    """Tests that the generated feed has the correct structure and required tags."""
    xml_str = rss.build_feed("test-user", sample_channel, sample_items)

    # 1. Assert namespaces are present in the raw XML string before parsing
    assert f'xmlns:itunes="{ITUNES_NS}"' in xml_str
    assert f'xmlns:atom="{ATOM_NS}"' in xml_str

    # 2. Parse the XML and validate content
    root = ET.fromstring(xml_str)

    assert root.tag == "rss"
    assert root.get("version") == "2.0"

    channel = root.find("channel")
    assert channel is not None

    assert channel.findtext("title") == sample_channel["title"]
    assert channel.findtext("link") == sample_channel["link"]
    assert channel.find("{" + ATOM_NS + "}link") is not None
    assert (
        channel.find("{" + ITUNES_NS + "}owner/{" + ITUNES_NS + "}name").text
        == sample_channel["owner_name"]
    )


def test_item_from_article(sample_items):
    """Tests the generation of a single <item> element."""
    item_meta = sample_items[0]
    item_el = rss.item_from_article(item_meta)

    assert item_el.findtext("title") == item_meta["title"]
    enclosure = item_el.find("enclosure")
    assert enclosure is not None
    assert enclosure.get("url") == item_meta["enclosure_url"]
    assert enclosure.get("type") == "audio/mpeg"
    assert enclosure.get("length") == str(item_meta["enclosure_length"])
    assert item_el.findtext("{" + ITUNES_NS + "}duration") == str(item_meta["duration"])
