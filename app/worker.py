from .services.jobs import get_job, update_job
from .services.extract import extract_article
from .services.tts import synthesize_article_to_mp3
from .services.store import save_article_record

def run_job(job_id: str):
    j = get_job(job_id)
    if not j: 
        return False, "job not found"
    if j["status"] == "done":
        return True, "already done"
    update_job(job_id, status="running")
    try:
        meta = extract_article(j["url"])
        audio_path, gcs_url = synthesize_article_to_mp3(meta, urlhash=j["urlhash"])
        rec = save_article_record(meta, audio_path, gcs_url, urlhash=j["urlhash"], uid=j["user_id"])
        update_job(job_id, status="done", audio_url=gcs_url, title=rec.get("title"))
        return True, "ok"
    except Exception as e:
        update_job(job_id, status="error", last_error=str(e))
        return False, str(e)
