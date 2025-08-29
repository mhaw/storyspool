#!/usr/bin/env bash
set -euo pipefail

# Automates minimal GCP setup to let Cloud Build push images to Artifact Registry
# - Enables required APIs
# - Optionally links billing if --billing-account is provided
# - Creates an Artifact Registry Docker repo if missing
# - Grants Cloud Build service account writer on the repo (project-level role)
# - Optionally enables Container Registry and grants Storage Admin for CR fallback
# - Optionally configures local Docker auth for AR
#
# Usage examples:
#   scripts/setup_gcp_permissions.sh --project storyspool-be776
#   scripts/setup_gcp_permissions.sh -p storyspool-be776 -l us -r storyspool-staging
#   scripts/setup_gcp_permissions.sh -p storyspool-be776 --billing-account=XXXX-XXXX-XXXX
#   scripts/setup_gcp_permissions.sh -p storyspool-be776 --also-container-registry
#

PROJECT_ID=""
AR_LOCATION="us"        # multi-region by default
AR_REPO="storyspool-staging"
BILLING_ACCOUNT=""
CONFIGURE_DOCKER_AUTH=true
ALSO_CR=false
GRANT_GCS=true
VERBOSE=false
GRANT_GCS=true

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
info() { printf "[info] %s\n" "$*"; }
warn() { printf "\033[33m[warn]\033[0m %s\n" "$*"; }
err()  { printf "\033[31m[error]\033[0m %s\n" "$*"; }

usage() {
  cat <<EOF
Usage: $0 [options]

Options:
  -p, --project PROJECT_ID         GCP project id (defaults to current gcloud project)
  -l, --location LOCATION          Artifact Registry location (default: us)
  -r, --repo REPO                  Artifact Registry repo name (default: storyspool-staging)
      --billing-account ACCOUNT    Billing account to link (format: XXXX-XXXX-XXXX)
      --no-docker-auth             Skip 'gcloud auth configure-docker'
      --also-container-registry    Also enable Container Registry and grant Storage Admin
      --no-gcs-iam                 Skip granting GCS IAM on Cloud Build bucket
      --verbose                    Enable verbose logging (trace commands)
  -h, --help                       Show this help

This script is idempotent and will create/enable only if missing.
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { err "Missing required command: $1"; exit 127; }
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project) PROJECT_ID="$2"; shift 2 ;;
    -l|--location) AR_LOCATION="$2"; shift 2 ;;
    -r|--repo) AR_REPO="$2"; shift 2 ;;
    --billing-account) BILLING_ACCOUNT="$2"; shift 2 ;;
    --no-docker-auth) CONFIGURE_DOCKER_AUTH=false; shift ;;
    --also-container-registry) ALSO_CR=true; shift ;;
    --no-gcs-iam) GRANT_GCS=false; shift ;;
    --verbose) VERBOSE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) err "Unknown argument: $1"; usage; exit 2 ;;
  esac
done

require_cmd gcloud

# Logging helpers with timestamps
ts() { date '+%Y-%m-%d %H:%M:%S'; }
step() { bold "[$(ts)] $*"; }

run() {
  local desc="$1"; shift || true
  step "$desc"
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
  local delay=2
  local i
  for ((i=1; i<=attempts; i++)); do
    "$@" && return 0 || true
    warn "Attempt $i failed. Retrying in ${delay}s ..."
    sleep "$delay"
    delay=$((delay*2))
  done
  err "All ${attempts} attempts failed for: $*"; return 1
}

# Determine project
if [[ -z "${PROJECT_ID}" ]]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi
if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  err "No project set. Use --project or 'gcloud config set project <id>'."; exit 2
fi

step "Using project: ${PROJECT_ID}"
run "Setting gcloud project" gcloud config set project "${PROJECT_ID}" >/dev/null

# Verify basic access and obtain project number
if ! PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)' 2>/dev/null); then
  err "Cannot describe project. Ensure you have at least roles/viewer on ${PROJECT_ID}."; exit 1
fi
step "Project Number: ${PROJECT_NUMBER}"
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Check billing and optionally link
billing_enabled=$(gcloud beta billing projects describe "${PROJECT_ID}" --format='value(billingEnabled)' 2>/dev/null || echo "false")
if [[ "${billing_enabled}" != "True" && "${billing_enabled}" != "true" ]]; then
  if [[ -n "${BILLING_ACCOUNT}" ]]; then
    run "Linking billing account ${BILLING_ACCOUNT} to ${PROJECT_ID}" gcloud beta billing projects link "${PROJECT_ID}" --billing-account="${BILLING_ACCOUNT}"
    info "Billing linked. It may take ~1 minute to propagate."
  else
    err "Billing not enabled for ${PROJECT_ID}. Provide --billing-account=XXXX-XXXX-XXXX or link via Console. Aborting to avoid stalls."
    exit 1
  fi
fi

# Enable required services
step "Enabling required services (Artifact Registry, Cloud Build${ALSO_CR:+, Container Registry})"
SERVICES=(artifactregistry.googleapis.com cloudbuild.googleapis.com)
if [[ "${ALSO_CR}" == true ]]; then
  SERVICES+=(containerregistry.googleapis.com)
fi
if ! retry 5 gcloud services enable "${SERVICES[@]}" --quiet; then
  err "Failed to enable some services. Ensure billing is enabled and you have roles/serviceusage.serviceUsageAdmin."; exit 1
fi

# Ensure AR repository exists
step "Ensuring Artifact Registry repo '${AR_REPO}' in '${AR_LOCATION}' exists"
if ! gcloud artifacts repositories describe "${AR_REPO}" --location="${AR_LOCATION}" >/dev/null 2>&1; then
  run "Creating Artifact Registry repo" gcloud artifacts repositories create "${AR_REPO}" \
    --repository-format=docker \
    --location="${AR_LOCATION}" \
    --description="Storyspool images" \
    --quiet
  info "Created repo ${AR_REPO} in ${AR_LOCATION}."
else
  info "Repo ${AR_REPO} already exists."
fi

# Grant IAM to Cloud Build service account
step "Granting Artifact Registry writer to Cloud Build service account"
retry 3 gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/artifactregistry.writer" \
  --quiet >/dev/null

if [[ "${ALSO_CR}" == true ]]; then
  step "Granting Storage Admin for Container Registry fallback"
  retry 3 gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/storage.admin" \
    --quiet >/dev/null
fi

# Grant GCS permissions on the Cloud Build bucket so builds can fetch source tarballs
if [[ "${GRANT_GCS}" == true ]]; then
  CBBUCKET="gs://${PROJECT_ID}_cloudbuild"
  step "Granting GCS IAM on ${CBBUCKET}"
  # Allow Cloud Build SA to manage objects in the Cloud Build bucket
  if ! gcloud storage buckets add-iam-policy-binding "${CBBUCKET}" \
      --member="serviceAccount:${CLOUD_BUILD_SA}" \
      --role="roles/storage.objectAdmin" \
      --quiet; then
    warn "gcloud storage failed; falling back to gsutil for Cloud Build SA."
    if command -v gsutil >/dev/null 2>&1; then
      gsutil iam ch serviceAccount:${CLOUD_BUILD_SA}:objectAdmin "${CBBUCKET}" || warn "gsutil failed to set IAM for Cloud Build SA."
    else
      warn "gsutil not found; skipping Cloud Build SA bucket IAM."
    fi
  fi

  # Also allow Compute Engine default SA to read objects (some builds may use it)
  COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
  if ! gcloud storage buckets add-iam-policy-binding "${CBBUCKET}" \
      --member="serviceAccount:${COMPUTE_SA}" \
      --role="roles/storage.objectViewer" \
      --quiet; then
    warn "gcloud storage failed; falling back to gsutil for Compute SA."
    if command -v gsutil >/dev/null 2>&1; then
      gsutil iam ch serviceAccount:${COMPUTE_SA}:objectViewer "${CBBUCKET}" || warn "gsutil failed to set IAM for Compute SA."
    else
      warn "gsutil not found; skipping Compute SA bucket IAM."
    fi
  fi
fi

# Configure docker auth if requested
if [[ "${CONFIGURE_DOCKER_AUTH}" == true ]]; then
  step "Configuring Docker auth for ${AR_LOCATION}-docker.pkg.dev"
  gcloud auth configure-docker "${AR_LOCATION}-docker.pkg.dev" --quiet || warn "Docker auth configuration failed (non-fatal)."
fi

step "Setup complete. Summary"
cat <<SUMMARY
- Project: ${PROJECT_ID} (${PROJECT_NUMBER})
- AR Location: ${AR_LOCATION}
- AR Repo: ${AR_REPO}
- Cloud Build SA: ${CLOUD_BUILD_SA}
- Services enabled: ${SERVICES[*]}
- Docker auth configured: ${CONFIGURE_DOCKER_AUTH}
SUMMARY

info "Default image reference would be: ${AR_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/storyspool-staging:<tag>"
