from google.cloud import firestore, storage

db = None
gcs = None


def init_extensions(app):
    global db, gcs
    db = (
        firestore.Client(project=app.config["GCP_PROJECT"])
        if app.config["GCP_PROJECT"]
        else firestore.Client()
    )
    gcs = (
        storage.Client(project=app.config["GCP_PROJECT"])
        if app.config["GCP_PROJECT"]
        else storage.Client()
    )
