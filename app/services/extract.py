from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urlparse
import trafilatura, requests
from bs4 import BeautifulSoup

@dataclass
class ArticleMeta:
    url: str
    title: str
    author: str|None
    text: str
    summary: str|None
    image: str|None
    site: str
    published: str|None
    canonical_url: str|None = None
    language: str|None = None

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
    return (link["href"].strip() if link and link.get("href") else None) or (og["content"].strip() if og and og.get("content") else url)

def extract_article(url: str) -> dict:
    downloaded = trafilatura.fetch_url(url)
    result = trafilatura.extract(downloaded, include_comments=False, include_tables=False, include_images=False, output="json")
    title = None; author=None; text=""; summary=None; image=None; published=None; canonical=None; lang=None
    if result:
        import json as _json
        data = _json.loads(result)
        title = data.get("title")
        author = (data.get("author","") or None)
        text = data.get("text","")
        summary = data.get("summary") or None
        image = data.get("image") or None
        published = data.get("date") or None
        canonical = data.get("source") or None
        lang = data.get("language") or None
    if not title or not text:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        html = resp.text
        if not title:
            title = _fallback_title(html)
        if not text:
            text = trafilatura.extract(html) or ""
        if not canonical:
            canonical = _canonical_url(html, url)
    site = urlparse(url).netloc
    meta = ArticleMeta(
        url=url, title=title or "Untitled", author=author, text=text, summary=summary,
        image=image, site=site, published=published, canonical_url=canonical, language=lang
    )
    return asdict(meta)
