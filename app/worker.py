import time

from flask import current_app  # New import

from .services.extract import extract_article
from .services.jobs import JobStatus, get_job, update_job
from .services.store import save_article_record
from .services.tts import synthesize_article_to_mp3


def run_job(job_id: str):
    job_start_time = time.time()
    j = get_job(job_id)
    content_id = j.get("urlhash", "unknown")

    log_extra = {"job_id": job_id, "content_id": content_id}

    current_app.logger.debug("Worker: Starting job", extra=log_extra)
    if not j:
        current_app.logger.error("Worker: Job not found.", extra=log_extra)
        return False, "job not found"
    if j["status"] == JobStatus.DONE:
        current_app.logger.debug("Worker: Job already done.", extra=log_extra)
        return True, "already done"

    try:
        # Stage 1: Fetching and Parsing
        stage_start_time = time.time()
        update_job(job_id, status=JobStatus.FETCHING)
        current_app.logger.debug("Worker: Fetching and parsing", extra=log_extra)
        meta = extract_article(j["url"])
        update_job(job_id, status=JobStatus.PARSING, title=meta.get("title"))
        stage_duration = time.time() - stage_start_time
        current_app.logger.info(
            "Worker: Fetching and parsing completed",
            extra={
                **log_extra,
                "stage": "fetch_parse",
                "duration": stage_duration,
                "status": JobStatus.PARSING,
            },
        )

        # Stage 2: TTS Generation
        stage_start_time = time.time()
        update_job(job_id, status=JobStatus.TTS_GENERATING)
        current_app.logger.debug("Worker: Synthesizing audio", extra=log_extra)
        audio_path, gcs_url = synthesize_article_to_mp3(meta, urlhash=j["urlhash"])
        stage_duration = time.time() - stage_start_time
        current_app.logger.info(
            "Worker: TTS generation completed",
            extra={
                **log_extra,
                "stage": "tts_generation",
                "duration": stage_duration,
                "status": JobStatus.TTS_GENERATING,
            },
        )

        # Stage 3: Uploading Audio
        stage_start_time = time.time()
        update_job(job_id, status=JobStatus.UPLOADING_AUDIO)
        current_app.logger.debug("Worker: Saving article record", extra=log_extra)
        rec = save_article_record(
            meta, audio_path, gcs_url, urlhash=j["urlhash"], uid=j["user_id"]
        )
        stage_duration = time.time() - stage_start_time
        current_app.logger.info(
            "Worker: Saving article record completed",
            extra={
                **log_extra,
                "stage": "upload_record",
                "duration": stage_duration,
                "status": JobStatus.UPLOADING_AUDIO,
            },
        )

        # Stage 4: Done
        job_duration = time.time() - job_start_time
        update_job(
            job_id,
            status=JobStatus.DONE,
            audio_url=gcs_url,
            title=rec.get("title"),
            processing_duration_seconds=round(job_duration),
        )
        current_app.logger.info(
            "Worker: Job completed successfully",
            extra={
                **log_extra,
                "stage": "done",
                "duration": job_duration,
                "status": JobStatus.DONE,
                "audio_url": gcs_url,
            },
        )
        return True, "ok"
    except Exception as e:
        job_duration = time.time() - job_start_time
        current_status = get_job(job_id).get("status", JobStatus.QUEUED)

        error_status_map = {
            JobStatus.FETCHING: JobStatus.FAILED_FETCH,
            JobStatus.PARSING: JobStatus.FAILED_PARSE,
            JobStatus.TTS_GENERATING: JobStatus.FAILED_TTS,
            JobStatus.UPLOADING_AUDIO: JobStatus.FAILED_UPLOAD,
        }
        error_status = error_status_map.get(current_status, JobStatus.FAILED_FETCH)

        user_friendly_error = "We couldn't process this URL. It might be a paywalled article, a video, or a page without a clear body of text. Please try a different URL."
        current_app.logger.error(
            "Worker: Job failed",
            exc_info=True,
            extra={
                **log_extra,
                "stage": "error",
                "duration": job_duration,
                "status": error_status,
                "error_class": e.__class__.__name__,
                "error_message": str(e),
            },
        )
        update_job(job_id, status=error_status, last_error=user_friendly_error)
        return False, str(e)
