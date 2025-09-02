import threading

from flask import current_app

from app.worker import run_job


def _run_job_with_context(app, job_id):
    with app.app_context():
        run_job(job_id)


def enqueue_worker(job_id: str):
    app = current_app._get_current_object()
    thread = threading.Thread(target=_run_job_with_context, args=(app, job_id))
    thread.daemon = True
    thread.start()
