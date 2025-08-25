from flask import Blueprint, render_template, request, jsonify, current_app, abort, flash
from .services.rss import user_feed_url, build_user_feed
from .services.users import current_user_id, require_login
from .services.store import list_user_articles
from .services.jobs import create_job, get_job
from .services.queue import enqueue_worker
from .services.security import validate_external_url
from .worker import run_job

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    uid = current_user_id()
    articles = list_user_articles(uid) if uid else []
    return render_template("index.html", articles=articles, feed_url=user_feed_url(uid) if uid else None)

@bp.post("/jobs")
@require_login
def create_ingest_job():
    url = (request.form.get("url") or (request.json or {}).get("url") or "").strip()
    if not url: return jsonify({"error":"missing url"}), 400
    ok, err = validate_external_url(url)
    if not ok: return jsonify({"error": f"invalid url: {err}"}), 400
    doc = create_job(url, current_user_id())
    enqueue_worker(doc["id"])
    flash("Job queued.")
    return jsonify({"job_id": doc["id"], "status": doc["status"]}), 202

@bp.get("/jobs/<job_id>")
def job_status(job_id):
    j = get_job(job_id)
    if not j: return jsonify({"error":"not found"}), 404
    return jsonify(j), 200

@bp.post("/task/worker")
def task_worker():
    if request.headers.get("X-Task-Token") != current_app.config["TASK_TOKEN"]:
        abort(403)
    job_id = (request.json or {}).get("job_id")
    ok, msg = run_job(job_id)
    return ({"ok": ok, "msg": msg}, 200 if ok else 500)

@bp.get("/u/<uid>/feed.xml")
def user_feed(uid):
    from flask import Response
    xml = build_user_feed(uid)
    return Response(xml, mimetype="application/rss+xml")
