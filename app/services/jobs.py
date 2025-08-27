from datetime import datetime, timezone
from hashlib import sha256

from flask import current_app  # New import

JOB_COL = "jobs"


class JobStatus:
    QUEUED = "queued"
    FETCHING = "fetching"
    PARSING = "parsing"
    TTS_GENERATING = "tts_generating"
    UPLOADING_AUDIO = "uploading_audio"
    DONE = "done"
    FAILED_FETCH = "failed_fetch"
    FAILED_PARSE = "failed_parse"
    FAILED_TTS = "failed_tts"
    FAILED_UPLOAD = "failed_upload"


def url_hash(url: str) -> str:
    return sha256(url.encode("utf-8")).hexdigest()[:12]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _jobs():
    db = current_app.config.get("FIRESTORE_DB")
    if db is None:
        raise RuntimeError(
            "Firestore client not initialized. FIRESTORE_DB is missing in app.config."
        )
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
        "status": JobStatus.QUEUED,
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


def list_user_jobs(uid: str):
    if not uid:
        return []
    qs = (
        _jobs()
        .where("user_id", "==", uid)
        .order_by("created_at", direction="DESCENDING")
        .limit(50)
        .stream()
    )
    return [q.to_dict() for q in qs]


def update_job(job_id: str, **fields):
    fields["updated_at"] = now_iso()
    if "metrics" in fields:
        fields["metrics"] = fields["metrics"]  # Ensure metrics are stored
    _jobs().document(job_id).set(fields, merge=True)
