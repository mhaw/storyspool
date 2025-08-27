from flask import current_app  # New import

from .services.extract import extract_article
from .services.jobs import get_job, update_job
from .services.store import save_article_record
from .services.tts import synthesize_article_to_mp3


def run_job(job_id: str):
    current_app.logger.debug(f"Worker: Starting job {job_id}")
    j = get_job(job_id)
    if not j:
        current_app.logger.error(f"Worker: Job {job_id} not found.")
        return False, "job not found"
    if j["status"] == "done":
        current_app.logger.debug(f"Worker: Job {job_id} already done.")
        return True, "already done"

    try:
        update_job(job_id, status="running")
        current_app.logger.debug(
            f"Worker: Extracting article for job {job_id} from {j["url"]}"
        )
        meta = extract_article(j["url"])

        current_app.logger.debug(f"Worker: Synthesizing audio for job {job_id}")
        audio_path, gcs_url = synthesize_article_to_mp3(meta, urlhash=j["urlhash"])

        current_app.logger.debug(f"Worker: Saving article record for job {job_id}")
        rec = save_article_record(
            meta, audio_path, gcs_url, urlhash=j["urlhash"], uid=j["user_id"]
        )

        update_job(job_id, status="done", audio_url=gcs_url, title=rec.get("title"))
        current_app.logger.info(
            f"Worker: Job {job_id} completed successfully. Audio URL: {gcs_url}"
        )
        return True, "ok"
    except Exception as e:
        current_app.logger.error(
            f"Worker: Job {job_id} failed: {e}", exc_info=True
        )  # Log traceback
        update_job(job_id, status="error", last_error=str(e))
        return False, str(e)
