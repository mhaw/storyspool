from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    render_template,
    request,
)

from .services.jobs import create_job, get_job
from .services.queue import enqueue_worker
from .services.rss import build_user_feed, user_feed_url
from .services.security import validate_external_url
from .services.store import list_user_articles
from .services.users import current_user_id, require_login
from .worker import run_job

bp = Blueprint("main", __name__)


@bp.get("/healthz")
def healthz():
    return "ok", 200


@bp.get("/health")
def health():
    return {"status": "ok"}, 200


@bp.get("/")
def index():
    uid = current_user_id()
    articles = list_user_articles(uid) if uid else []
    return render_template(
        "index.html", articles=articles, feed_url=user_feed_url(uid) if uid else None
    )


@bp.post("/jobs")
@require_login
def create_ingest_job():
    url = (request.form.get("url") or (request.json or {}).get("url") or "").strip()
    if not url:
        return jsonify({"error": "missing url"}), 400
    ok, err = validate_external_url(url)
    if not ok:
        return jsonify({"error": f"invalid url: {err}"}), 400
    doc = create_job(url, current_user_id())
    enqueue_worker(doc["id"])
    flash("Job queued.")
    return jsonify({"job_id": doc["id"], "status": doc["status"]}), 202


@bp.get("/jobs/<job_id>")
def job_status(job_id):
    j = get_job(job_id)
    if not j:
        return jsonify({"error": "not found"}), 404
    return jsonify(j), 200


@bp.post("/task/worker")
def task_worker():
    provided_token = request.headers.get("X-Task-Token")
    expected_token = current_app.config["TASK_TOKEN"]

    if provided_token != expected_token:
        current_app.logger.warning("Task token mismatch. Aborting 403.")
        abort(403)

    current_app.logger.debug(
        f"Received /task/worker request. request.json: {request.json}"
    )
    job_id = (request.json or {}).get("job_id")

    if not job_id:
        current_app.logger.error("Missing job_id in /task/worker request.")
        return ({"ok": False, "msg": "Missing job_id"}, 400)

    ok, msg = run_job(job_id)
    return ({"ok": ok, "msg": msg}, 200 if ok else 500)


@bp.get("/u/<uid>/feed.xml")
def user_feed(uid):
    from flask import Response

    xml = build_user_feed(uid)
    return Response(xml, mimetype="application/rss+xml")


@bp.get("/_health/firestore")
def firestore_health_check():
    from flask import current_app

    try:
        db = current_app.config.get("FIRESTORE_DB")
        if db is None:
            return {
                "status": "error",
                "message": "Firestore client not found in app config",
            }, 500
        # Attempt a simple operation to confirm connectivity
        # This assumes you have a collection named 'health_check' and a document 'test'
        # You might need to create these manually in the emulator UI if they don't exist
        db.collection("health_check").document("test").get()
        return {
            "status": "ok",
            "message": "Firestore client initialized and connected",
        }, 200
    except Exception as e:
        return {"status": "error", "message": f"Firestore connection failed: {e}"}, 500
