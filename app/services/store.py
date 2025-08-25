import pathlib
import uuid
from datetime import datetime, timezone

from flask import current_app

from ..extensions import db, gcs
from .users import current_user_id


def _articles_col():
    return db.collection(current_app.config["FIRESTORE_COLLECTION"])


def save_article_record(
    meta: dict, local_audio_path: str, gcs_url: str, urlhash: str, uid: str
):
    doc = {
        "id": urlhash,
        "user_id": uid,
        "title": meta.get("title"),
        "url": meta.get("url"),
        "canonical_url": meta.get("canonical_url"),
        "site": meta.get("site"),
        "summary": meta.get("summary"),
        "author": meta.get("author"),
        "image": meta.get("image"),
        "published": meta.get("published"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "audio_url": gcs_url,
    }
    _articles_col().document(urlhash).set(doc, merge=True)
    return doc


def list_user_articles(uid: str):
    if not uid:
        return []
    qs = (
        _articles_col()
        .where("user_id", "==", uid)
        .order_by("created_at", direction="DESCENDING")
        .limit(50)
        .stream()
    )
    return [q.to_dict() for q in qs]


def upload_audio_and_get_url(
    local_path: pathlib.Path, meta: dict, urlhash: str | None = None
) -> str:
    bucket = gcs.bucket(current_app.config["GCS_BUCKET"])
    key = f"audio/{urlhash or 'unknown'}/{datetime.now().strftime('%Y%m%d')}/{local_path.name}"
    blob = bucket.blob(key)
    blob.upload_from_filename(str(local_path))
    blob.make_public()
    return blob.public_url
