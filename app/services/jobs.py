from datetime import datetime, timezone
from hashlib import sha256

from ..extensions import db

JOB_COL = "jobs"


def url_hash(url: str) -> str:
    return sha256(url.encode("utf-8")).hexdigest()[:12]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _jobs():
    return db.collection(JOB_COL)


def create_job(url: str, uid: str) -> dict:
    h = url_hash(url)
    snap = _jobs().document(h).get()
    if snap.exists:
        return snap.to_dict()
    doc = {
        "id": h,
        "url": url,
        "urlhash": h,
        "user_id": uid,
        "status": "queued",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_error": None,
        "audio_url": None,
        "title": None,
    }
    _jobs().document(h).set(doc)
    return doc


def get_job(job_id: str) -> dict | None:
    s = _jobs().document(job_id).get()
    return s.to_dict() if s.exists else None


def update_job(job_id: str, **fields):
    fields["updated_at"] = now_iso()
    _jobs().document(job_id).set(fields, merge=True)
