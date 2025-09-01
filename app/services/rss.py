from datetime import datetime, timezone
from email.utils import formatdate
from xml.etree import ElementTree as ET

from flask import current_app

from app.services.jobs import list_user_jobs
from app.services.store import list_user_articles  # New import

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"


def _rfc822(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return formatdate(dt.timestamp(), usegmt=True)


def item_from_article(meta: dict) -> ET.Element:
    """Builds an RSS <item> from article metadata."""
    item = ET.Element("item")
    ET.SubElement(item, "title").text = meta.get("title", "(no title)")
    ET.SubElement(item, "guid", attrib={"isPermaLink": "false"}).text = meta["guid"]
    ET.SubElement(item, "pubDate").text = _rfc822(meta["pub_date"])
    ET.SubElement(item, "link").text = meta.get("source_url", "")
    ET.SubElement(item, "description").text = meta.get("summary", "")

    enclosure = ET.SubElement(item, "enclosure")
    enclosure.set("url", meta["enclosure_url"])
    enclosure.set("type", "audio/mpeg")
    if "enclosure_length" in meta and meta["enclosure_length"]:
        enclosure.set("length", str(meta["enclosure_length"]))

    ET.SubElement(item, "{" + ITUNES_NS + "}author").text = meta.get(
        "author", "StorySpool"
    )
    ET.SubElement(item, "{" + ITUNES_NS + "}summary").text = meta.get("summary", "")
    if "duration" in meta:
        ET.SubElement(item, "{" + ITUNES_NS + "}duration").text = str(meta["duration"])

    return item


def build_feed(user_id: str, channel_info: dict, items_meta: list[dict]) -> str:
    """Builds the complete RSS XML string for a user's podcast feed."""
    ET.register_namespace("itunes", ITUNES_NS)
    ET.register_namespace("atom", ATOM_NS)

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = channel_info["title"]
    ET.SubElement(channel, "link").text = channel_info["link"]
    ET.SubElement(channel, "description").text = channel_info.get("description", "")
    ET.SubElement(channel, "language").text = channel_info.get("language", "en-us")
    ET.SubElement(channel, "lastBuildDate").text = _rfc822(datetime.now(timezone.utc))

    atom_link = ET.SubElement(channel, "{" + ATOM_NS + "}link")
    atom_link.set("href", channel_info["link"])
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    ET.SubElement(channel, "{" + ITUNES_NS + "}author").text = channel_info.get(
        "author", "StorySpool"
    )
    owner = ET.SubElement(channel, "{" + ITUNES_NS + "}owner")
    ET.SubElement(owner, "{" + ITUNES_NS + "}name").text = channel_info.get(
        "owner_name", "StorySpool"
    )
    ET.SubElement(owner, "{" + ITUNES_NS + "}email").text = channel_info.get(
        "owner_email", "support@storyspool.com"
    )
    ET.SubElement(channel, "{" + ITUNES_NS + "}explicit").text = "no"
    ET.SubElement(channel, "{" + ITUNES_NS + "}category", attrib={"text": "News"})
    if "image_url" in channel_info:
        image = ET.SubElement(channel, "{" + ITUNES_NS + "}image")
        image.set("href", channel_info["image_url"])

    for meta in items_meta:
        channel.append(item_from_article(meta))

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")


def get_latest_items_for_user(user_id: str, limit: int = 100) -> list[dict]:
    """Fetches latest processed articles and directly submitted articles for a user."""
    all_items = []

    # Fetch articles from jobs (processed articles)
    jobs = list_user_jobs(user_id, limit=limit, status="COMPLETED")
    for job in jobs:
        if not job.get("storage_path"):
            continue
        public_audio_url = f"https://storage.googleapis.com/{current_app.config['GCS_BUCKET_NAME']}/{job['storage_path']}"
        all_items.append(
            {
                "guid": job["job_id"],
                "title": job.get("article_title", "Untitled Article"),
                "summary": job.get("article_summary", ""),
                "pub_date": job.get("created_at", datetime.now(timezone.utc)),
                "source_url": job.get("article_url", ""),
                "enclosure_url": public_audio_url,
                "enclosure_length": job.get("audio_size_bytes", 0),
                "duration": job.get("audio_duration_seconds", 0),
                "author": job.get("article_author", "StorySpool"),
                "type": "job",  # Add type for debugging/distinction
            }
        )

    # Fetch articles submitted directly (not yet processed into audio)
    submitted_articles = list_user_articles(user_id)
    for article in submitted_articles:
        # For directly submitted articles, there's no audio yet.
        # We'll use a placeholder or indicate it's not available.
        # The guid should be unique, using the urlhash from Firestore.
        all_items.append(
            {
                "guid": article["id"],  # Using the urlhash as guid
                "title": article.get("title", "Untitled Submitted Article"),
                "summary": article.get("summary", ""),
                "pub_date": (
                    datetime.fromisoformat(article["created_at"])
                    if "created_at" in article
                    else datetime.now(timezone.utc)
                ),
                "source_url": article.get("url", ""),
                "enclosure_url": article.get(
                    "audio_url", ""
                ),  # Will be empty initially
                "enclosure_length": 0,  # No audio yet
                "duration": 0,  # No audio yet
                "author": article.get("author", "StorySpool"),
                "type": "submitted",  # Add type for debugging/distinction
            }
        )

    # Sort all items by publication date (newest first)
    return sorted(all_items, key=lambda x: x["pub_date"], reverse=True)[:limit]
