import datetime
import hashlib

from firebase_admin import auth
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from .services import rss
from .services.extract import extract_article
from .services.jobs import JobStatus, create_job, get_job, list_user_jobs, update_job
from .services.queue import enqueue_worker
from .services.security import validate_external_url
from .services.store import save_article_record
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
    if uid:
        return redirect(url_for("main.article_list"))
    return render_template("index.html", firebase_config=current_app.config["FIREBASE"])


@bp.post("/sessionLogin")
def session_login():
    """Creates a session cookie from a Firebase ID token."""
    id_token = request.json.get("idToken")
    if not id_token:
        return jsonify({"error": "Missing ID token"}), 400

    try:
        # Set session expiration to 5 days.
        expires_in = datetime.timedelta(days=5)
        session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)
        response = jsonify({"status": "success"})
        expires = datetime.datetime.now() + expires_in
        response.set_cookie(
            current_app.config["COOKIE_NAME"],
            session_cookie,
            expires=expires,
            httponly=True,
            secure=current_app.config["SESSION_COOKIE_SECURE"],
            samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
        )
        return response
    except Exception as e:
        current_app.logger.error(f"Failed to create session cookie: {e}")
        return jsonify({"error": "Failed to create session cookie"}), 401


@bp.post("/logout")
def logout():
    """Clears the session cookie."""
    response = make_response(jsonify({"status": "success"}))
    response.set_cookie(
        current_app.config["COOKIE_NAME"],
        "",
        expires=0,
        httponly=True,
        secure=current_app.config["SESSION_COOKIE_SECURE"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
    )
    return response


@bp.get("/articles")
@require_login
def article_list():
    uid = current_user_id()
    jobs = list_user_jobs(uid)
    feed_url = url_for("main.user_feed", uid=uid, _external=True)  # noqa: F841
    return render_template(
        "articles.html",
        jobs=jobs,
        feed_url=feed_url,
        firebase_config=current_app.config["FIREBASE"],
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


@bp.post("/jobs/<job_id>/retry")
@require_login
def retry_ingest_job(job_id):
    # Optional: check if user is allowed to retry this job
    update_job(job_id, status=JobStatus.QUEUED, last_error=None)
    enqueue_worker(job_id)
    return jsonify({"status": "re-queued"}), 200


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
@require_login
def user_feed(uid):
    """Generates the user's podcast feed on-demand with caching."""
    if not uid or uid != current_user_id():
        current_app.logger.warning(
            "Attempted to access feed for another user or with empty UID."
        )
        abort(403, description="Forbidden")

    try:
        items = rss.get_latest_items_for_user(uid, limit=100)

        user = {
            "user_id": uid
        }  # Replace with actual user lookup if needed for more details
        user_articles_url = url_for("main.article_list", _external=True)

        channel = {
            "title": f"StorySpool Feed for {user['user_id']}",
            "link": user_articles_url,
            "description": "Your personal feed of narrated articles from StorySpool.",
            "author": "StorySpool",
            "owner_name": "StorySpool",
            "owner_email": "support@storyspool.com",
            "image_url": url_for(
                "static", filename="brand/storyspool_mark.svg", _external=True
            ),
        }

        xml = rss.build_feed(uid, channel, items)

        resp = Response(xml, mimetype="application/rss+xml; charset=utf-8")
        resp.headers["Cache-Control"] = "public, max-age=300"  # Cache for 5 minutes
        return resp
    except Exception as e:
        current_app.logger.exception(f"Error generating RSS feed for user {uid}: {e}")
        # Return an empty, but valid, RSS feed to prevent client crashes
        empty_xml = rss.build_feed(
            uid,
            {
                "title": f"Error Feed for {uid}",
                "link": url_for("main.article_list", _external=True),
                "description": "There was an error generating this feed.",
                "author": "StorySpool",
                "owner_name": "StorySpool",
                "owner_email": "support@storyspool.com",
            },
            [],
        )
        resp = Response(empty_xml, mimetype="application/rss+xml; charset=utf-8")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.status_code = 500
        return resp


@bp.get("/_health/firestore")
def firestore_health_check():
    from flask import current_app

    try:
        db = current_app.config.get("FIRESTORE_DB")
        if db is None:
            return (
                {
                    "status": "error",
                    "message": "Firestore client not found in app config",
                },
                500,
            )
        # Attempt a simple operation to confirm connectivity
        db.collection("health_check").document("test").get()
        return (
            {
                "status": "ok",
                "message": "Firestore client initialized and connected",
            },
            200,
        )
    except Exception as e:
        return {"status": "error", "message": f"Firestore connection failed: {e}"}, 500
