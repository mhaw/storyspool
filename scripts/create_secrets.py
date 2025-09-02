import os

from google.cloud import secretmanager

project_id = os.environ.get("GCP_PROJECT")
if not project_id:
    print("Please set the GCP_PROJECT environment variable.")
    exit()

secrets_to_create = {
    "firebase-api-key": "FIREBASE_API_KEY",
    "firebase-project-id": "FIREBASE_PROJECT_ID",
    "firebase-auth-domain": "FIREBASE_AUTH_DOMAIN",
    "firebase-app-id": "FIREBASE_APP_ID",
    "firebase-measurement-id": "FIREBASE_MEASUREMENT_ID",
    "task-token": "TASK_TOKEN",
}

client = secretmanager.SecretManagerServiceClient()

for secret_id, env_var in secrets_to_create.items():
    secret_value = os.environ.get(env_var)
    if not secret_value:
        print(
            f"Please set the environment variable '{env_var}' for the secret '{secret_id}'."
        )
        continue

    parent = f"projects/{project_id}"

    # Create the secret
    try:
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        print(f"Secret '{secret_id}' created.")
    except Exception as e:
        if "already exists" in str(e):
            print(f"Secret '{secret_id}' already exists.")
        else:
            print(f"Error creating secret '{secret_id}': {e}")
            continue

    # Add the secret version
    try:
        parent = client.secret_path(project_id, secret_id)
        response = client.add_secret_version(
            request={
                "parent": parent,
                "payload": {"data": secret_value.encode("UTF-8")},
            }
        )
        print(f"Added secret version for '{secret_id}'.")
    except Exception as e:
        print(f"Error adding secret version for '{secret_id}': {e}")
