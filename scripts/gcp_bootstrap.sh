#!/usr/bin/env bash
# StorySpool — GCP bootstrap (project-wide). Idempotent where possible.
# Usage: ./gcp_bootstrap.sh <PROJECT_ID> <REGION(us-central1 default)>
set -euo pipefail
PROJECT_ID="${1:?PROJECT_ID required}"
REGION="${2:-us-central1}"
QUEUE="speakaudio2-jobs"
SA_NAME="speakaudio2-sa"
STAGING_BUCKET="speakaudio2-audio-staging"
PROD_BUCKET="speakaudio2-audio-prod"
TASK_SECRET="SPEAKAUDIO2_TASK_TOKEN"

echo "==> Setting project"
gcloud config set project "$PROJECT_ID"

echo "==> Enabling APIs"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  texttospeech.googleapis.com firestore.googleapis.com storage.googleapis.com \
  cloudtasks.googleapis.com secretmanager.googleapis.com iamcredentials.googleapis.com

echo "==> Firestore (ensure Native mode is created in console if not)"
# No CLI to create DB in Native mode reliably; prompt user if missing
gcloud firestore databases describe || echo "If missing, open Console → Firestore → Create DB (Native)."

echo "==> Buckets"
gsutil ls -b "gs://${STAGING_BUCKET}" || gsutil mb -l "$REGION" "gs://${STAGING_BUCKET}"
gsutil ls -b "gs://${PROD_BUCKET}" || gsutil mb -l "$REGION" "gs://${PROD_BUCKET}"

echo "==> Cloud Tasks queue"
gcloud tasks queues describe "$QUEUE" --location="$REGION" >/dev/null 2>&1 || \
  gcloud tasks queues create "$QUEUE" --location="$REGION" \
    --max-attempts=3 --max-dispatches-per-second=5 --max-concurrent-dispatches=5

echo "==> Service Account"
gcloud iam service-accounts list --format="value(email)" | grep -q "^${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com$" || \
  gcloud iam service-accounts create "$SA_NAME" --display-name="StorySpool Runtime"

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Granting roles to ${SA_EMAIL}"
for ROLE in roles/run.invoker roles/storage.objectAdmin roles/firestore.user roles/texttospeech.user roles/cloudtasks.enqueuer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" --role="$ROLE" >/dev/null
done

echo "==> Secret Manager token (TASK token)"
if ! gcloud secrets describe "${TASK_SECRET}" >/dev/null 2>&1; then
  RAND=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)
  echo -n "$RAND" | gcloud secrets create "${TASK_SECRET}" --data-file=-
else
  echo "(Secret ${TASK_SECRET} exists)"
fi

echo "==> Grant secret access to runtime SA"
gcloud secrets add-iam-policy-binding "${TASK_SECRET}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" >/dev/null

echo "==> Summary"
cat <<EOF
PROJECT_ID=$PROJECT_ID
REGION=$REGION
SERVICE_ACCOUNT=$SA_EMAIL
STAGING_BUCKET=gs://${STAGING_BUCKET}
PROD_BUCKET=gs://${PROD_BUCKET}
TASKS_QUEUE=${QUEUE}
TASKS_LOCATION=${REGION}
TASK_TOKEN_SECRET=${TASK_SECRET}

Next steps:
1) Create two Cloud Run services (staging/prod) using ${SA_EMAIL}.
2) In each service, set env vars:
   ENV=staging|prod
   GCP_PROJECT=${PROJECT_ID}
   FIRESTORE_COLLECTION=articles_staging|articles
   GCS_BUCKET=${STAGING_BUCKET}|${PROD_BUCKET}
   TASKS_QUEUE=${QUEUE}
   TASKS_LOCATION=${REGION}
   TASK_TOKEN (mounted from Secret ${TASK_SECRET})
3) Set BASE_URL to each service URL after first deploy.
EOF
