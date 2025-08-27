from dataclasses import asdict, dataclass
from urllib.parse import urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup


@dataclass
class ArticleMeta:
    url: str
    title: str
    author: str | None
    text: str
    summary: str | None
    image: str | None
    site: str
    published: str | None
    canonical_url: str | None = None
    language: str | None = None


def _fallback_title(html):
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    og = soup.find("meta", property="og:title")
    return og["content"].strip() if og and og.get("content") else "Untitled"


def _canonical_url(html, url):
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("link", rel="canonical")
    og = soup.find("meta", property="og:url")
    return (link["href"].strip() if link and link.get("href") else None) or (
        og["content"].strip() if og and og.get("content") else url
    )


def extract_article(url: str) -> dict:
    downloaded = trafilatura.fetch_url(url)
    result = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
        include_images=False,
        output="json",
    )
    data = {}  # Initialize data as empty dict
    if result:
        import json as _json

        from flask import \
            current_app  # Ensure current_app is imported for logging

        try:
            data = _json.loads(result)
        except _json.JSONDecodeError:
            current_app.logger.warning(
                f"Trafilatura returned invalid JSON for {url}. Falling back to HTML parsing."
            )
            data = {}  # Reset data if JSON parsing fails

    title = data.get("title")
    author = data.get("author", "") or None
    text = data.get("text", "")
    summary = data.get("summary") or None
    image = data.get("image") or None
    published = data.get("date") or None
    canonical = data.get("source") or None
    lang = data.get("language") or None

    # Fallback to direct HTML parsing if structured data is missing or JSON parsing failed
    if not title or not text:
        # Ensure current_app is imported for logging
        from flask import current_app

        current_app.logger.debug(f"Falling back to direct HTML parsing for {url}")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        html = resp.text
        if not title:
            title = _fallback_title(html)
        if not text:
            text = trafilatura.extract(html) or ""  # Extract plain text
        if not canonical:
            canonical = _canonical_url(html, url)
    site = urlparse(url).netloc
    meta = ArticleMeta(
        url=url,
        title=title or "Untitled",
        author=author,
        text=text,
        summary=summary,
        image=image,
        site=site,
        published=published,
        canonical_url=canonical,
        language=lang,
    )
    return asdict(meta)
