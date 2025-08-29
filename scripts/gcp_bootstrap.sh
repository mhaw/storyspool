#!/usr/bin/env bash
# StorySpool — GCP bootstrap (project-wide). Idempotent and comprehensive.
# Sets up resources for both building (CI/CD) and running the application.
#
# Usage: ./gcp_bootstrap.sh [--project <id>] [--region <name>] [--billing-account <id>]
#
# Based on original gcp_bootstrap.sh and setup_gcp_permissions.sh

set -euo pipefail

# === Configuration ===
# These variables can be customized.
# GCP Settings
DEFAULT_REGION="us-central1"
# Artifact Registry Settings
AR_REPO="storyspool-images"
# Application Settings
RUNTIME_SA_NAME="storyspool-runtime-sa"
STAGING_BUCKET_SUFFIX="audio-staging"
PROD_BUCKET_SUFFIX="audio-prod"
TASKS_QUEUE="storyspool-jobs"
TASK_SECRET_NAME="STORYSPOOL_TASK_TOKEN"

# === Script State ===
PROJECT_ID=""
REGION=""
BILLING_ACCOUNT=""
VERBOSE=false

# === Helper Functions ===
bold() { printf "\033[1m%s\033[0m\n" "$*"; }
info() { printf "[info] %s\n" "$*"; }
warn() { printf "\033[33m[warn]\033[0m %s\n" "$*"; }
err()  { printf "\033[31m[error]\033[0m %s\n" "$*"; exit 1; }
ts() { date '+%Y-%m-%d %H:%M:%S'; }
step() { bold "[$(ts)] $*"; }

usage() {
  cat <<EOF
Usage: $0 [options]

This script sets up all necessary GCP resources for the StorySpool project,
including services for CI/CD (Cloud Build, Artifact Registry) and for the
application runtime (Cloud Run, Firestore, Storage, Tasks, Secret Manager).

It is designed to be idempotent and can be re-run safely.

Options:
  -p, --project <id>         GCP project ID. If not provided, attempts to use the
                             currently configured gcloud project.
  -r, --region <name>        GCP region for regional resources.
                             (default: ${DEFAULT_REGION})
  -b, --billing-account <id> Billing account to link (e.g., XXXX-XXXX-XXXX).
                             Required if the project has no billing account.
      --verbose              Enable verbose logging to trace commands.
  -h, --help                 Show this help message.
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || err "Missing required command: '$1'. Please install it."
}

run() {
  local desc="$1"; shift
  info "$desc"
  if [[ "$VERBOSE" == true ]]; then
    set -x
  fi
  "$@"
  local rc=$?
  if [[ "$VERBOSE" == true ]]; then
    set +x
  fi
  return $rc
}

retry() {
  local attempts=$1; shift
  local delay=3
  for ((i=1; i<=attempts; i++)); do
    "$@" && return 0
    warn "Attempt $i/$attempts failed. Retrying in ${delay}s..."
    sleep "$delay"
    delay=$((delay*2))
  done
  err "All ${attempts} attempts failed for command: $*"
}

# === Argument Parsing ===
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project) PROJECT_ID="$2"; shift 2 ;;
    -r|--region) REGION="$2"; shift 2 ;;
    -b|--billing-account) BILLING_ACCOUNT="$2"; shift 2 ;;
    --verbose) VERBOSE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) err "Unknown argument: $1";;
  esac
done

# === Main Logic ===
main() {
  require_cmd gcloud
  require_cmd gsutil
  require_cmd openssl

  # --- 1. Project and Billing Setup ---
  step "1. Verifying Project and Billing"
  if [[ -z "${PROJECT_ID}" ]]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    [[ -z "${PROJECT_ID}" ]] && err "No GCP project specified. Use --project or run 'gcloud config set project <id>'."
    info "Using active project: ${PROJECT_ID}"
  fi
  run "Setting gcloud project context" gcloud config set project "${PROJECT_ID}" >/dev/null

  if ! PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)' 2>/dev/null); then
    err "Cannot describe project '${PROJECT_ID}'. Ensure it exists and you have 'roles/browser' permission."
  fi
  info "Project: ${PROJECT_ID} (Number: ${PROJECT_NUMBER})"

  local billing_enabled
  billing_enabled=$(gcloud beta billing projects describe "${PROJECT_ID}" --format='value(billingEnabled)' 2>/dev/null || echo "false")
  if [[ "${billing_enabled}" != "True" ]]; then
    if [[ -n "${BILLING_ACCOUNT}" ]]; then
      run "Linking billing account ${BILLING_ACCOUNT}" \
        gcloud beta billing projects link "${PROJECT_ID}" --billing-account="${BILLING_ACCOUNT}" --quiet
      info "Billing linked. It may take a minute to propagate."
      sleep 10 # Give time for billing to propagate
    else
      err "Billing is not enabled for project '${PROJECT_ID}'. Please link a billing account in the GCP console or use the --billing-account flag."
    fi
  else
    info "Billing is already enabled."
  fi

  # --- 2. API Enablement ---
  step "2. Enabling required GCP APIs"
  local apis_to_enable=(
    run.googleapis.com
    cloudbuild.googleapis.com
    artifactregistry.googleapis.com
    texttospeech.googleapis.com
    firestore.googleapis.com
    storage.googleapis.com
    cloudtasks.googleapis.com
    secretmanager.googleapis.com
    iamcredentials.googleapis.com
    iam.googleapis.com
  )
  run "Enabling ${#apis_to_enable[@]} APIs" \
    retry 3 gcloud services enable "${apis_to_enable[@]}" --quiet

  # --- 3. CI/CD Setup (Artifact Registry & Cloud Build Permissions) ---
  step "3. Setting up CI/CD resources"
  REGION=${REGION:-$DEFAULT_REGION}
  info "Using region: ${REGION}"

  if ! gcloud artifacts repositories describe "${AR_REPO}" --location="${REGION}" >/dev/null 2>&1; then
    run "Creating Artifact Registry repository '${AR_REPO}'" \
      gcloud artifacts repositories create "${AR_REPO}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="StorySpool container images" \
        --quiet
  else
    info "Artifact Registry repository '${AR_REPO}' already exists."
  fi

  local cloud_build_sa="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
  info "Granting Cloud Build SA (${cloud_build_sa}) permissions..."
  run "Granting Artifact Registry Writer role" \
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${cloud_build_sa}" \
      --role="roles/artifactregistry.writer" --condition=None >/dev/null

  # --- 4. Application Runtime Setup ---
  step "4. Setting up Application Runtime resources"
  local runtime_sa_email="${RUNTIME_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

  if ! gcloud iam service-accounts describe "${runtime_sa_email}" >/dev/null 2>&1; then
    run "Creating runtime Service Account '${RUNTIME_SA_NAME}'" \
      gcloud iam service-accounts create "${RUNTIME_SA_NAME}" --display-name="StorySpool Runtime Account"
  else
    info "Runtime Service Account '${RUNTIME_SA_NAME}' already exists."
  fi

  info "Granting runtime SA roles..."
  local roles_to_grant=(
    roles/run.invoker
    roles/storage.objectCreator
    roles/storage.objectViewer
    roles/datastore.user

    roles/cloudtasks.enqueuer
    roles/secretmanager.secretAccessor
  )
  for role in "${roles_to_grant[@]}"; do
    run "Granting ${role}" \
      gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${runtime_sa_email}" \
        --role="$role" --condition=None >/dev/null
  done

  step "4a. Firestore Database"
  if ! gcloud firestore databases describe --location=$REGION >/dev/null 2>&1; then
     warn "Firestore database not found in region ${REGION}."
     warn "Please create one manually in the GCP console: Firestore -> Create Database -> Native Mode."
  else
     info "Firestore database already exists."
  fi

  step "4b. Cloud Storage Buckets"
  local staging_bucket_name="${PROJECT_ID}-${STAGING_BUCKET_SUFFIX}"
  local prod_bucket_name="${PROJECT_ID}-${PROD_BUCKET_SUFFIX}"
  run "Ensuring staging bucket exists: gs://${staging_bucket_name}" \
    gsutil ls -b "gs://${staging_bucket_name}" || gsutil mb -l "$REGION" "gs://${staging_bucket_name}"
  run "Ensuring prod bucket exists: gs://${prod_bucket_name}" \
    gsutil ls -b "gs://${prod_bucket_name}" || gsutil mb -l "$REGION" "gs://${prod_bucket_name}"

  step "4c. Cloud Tasks Queue"
  if ! gcloud tasks queues describe "$TASKS_QUEUE" --location="$REGION" >/dev/null 2>&1; then
    run "Creating Cloud Tasks queue '${TASKS_QUEUE}'" \
      gcloud tasks queues create "$TASKS_QUEUE" --location="$REGION" \
        --max-attempts=3 --max-dispatches-per-second=5 --max-concurrent-dispatches=5
  else
    info "Cloud Tasks queue '${TASKS_QUEUE}' already exists."
  fi

  step "4d. Secret Manager Secret"
  if ! gcloud secrets describe "${TASK_SECRET_NAME}" >/dev/null 2>&1; then
    info "Creating secret '${TASK_SECRET_NAME}'..."
    local rand_token
    rand_token=$(openssl rand -base64 32)
    echo -n "$rand_token" | gcloud secrets create "${TASK_SECRET_NAME}" --data-file=-
  else
    info "Secret '${TASK_SECRET_NAME}' already exists."
  fi
  # IAM for secret is granted with the other runtime roles.

  # --- 5. Summary and Next Steps ---
  step "✅ GCP Bootstrap Complete!"
  bold "Summary of Resources:"
  cat <<EOF
--------------------------------------------------
Project Information
  Project ID:         ${PROJECT_ID}
  Project Number:     ${PROJECT_NUMBER}
  Region:             ${REGION}

CI/CD Resources
  Cloud Build SA:     ${cloud_build_sa}
  Artifact Registry:  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}

Application Runtime Resources
  Runtime SA:         ${runtime_sa_email}
  Staging Bucket:     gs://${staging_bucket_name}
  Prod Bucket:        gs://${prod_bucket_name}
  Tasks Queue:        ${TASKS_QUEUE}
  Task Token Secret:  ${TASK_SECRET_NAME}
--------------------------------------------------
EOF

  bold "Next Steps:"
  echo "1. Deploy Firestore rules and indexes:"
  echo "   firebase deploy --only firestore"
  echo ""
  echo "2. Configure and deploy your Cloud Run services (staging/prod)."
  echo "   - Use the runtime service account: ${runtime_sa_email}"
  echo "   - Mount the task token secret: ${TASK_SECRET_NAME}"
  echo "   - Set environment variables for each service (e.g., GCS_BUCKET, ENV)."
  echo ""
  echo "3. If using GitHub Actions for CI/CD, run the WIF setup script:"
  echo "   ./scripts/github_wif_setup.sh ${PROJECT_ID} <YOUR_GH_ORG> <YOUR_GH_REPO>"
  echo ""
  echo "4. Configure local Docker to push to Artifact Registry:"
  echo "   gcloud auth configure-docker ${REGION}-docker.pkg.dev"
}

main "$@"
