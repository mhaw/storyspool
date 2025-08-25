import json
from google.cloud import tasks_v2
from flask import current_app

def enqueue_worker(job_id: str):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(current_app.config["GCP_PROJECT"],
                               current_app.config["TASKS_LOCATION"],
                               current_app.config["TASKS_QUEUE"])
    url = f"{current_app.config['BASE_URL']}/task/worker"
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json", "X-Task-Token": current_app.config["TASK_TOKEN"]},
            "body": json.dumps({"job_id": job_id}).encode(),
        }
    }
    return client.create_task(request={"parent": parent, "task": task}).name
