#!/usr/bin/env bash
# StorySpool — GitHub Workload Identity Federation quick-setup
# Usage: ./github_wif_setup.sh <PROJECT_ID> <GH_ORG_OR_USER> <GH_REPO> <POOL_NAME:github-pool> <PROVIDER_NAME:github-provider>
set -euo pipefail
PROJECT_ID="${1:?PROJECT_ID required}"
GH_OWNER="${2:?GitHub org/user required}"
GH_REPO="${3:?GitHub repo name required}"
POOL="${4:-github-pool}"
PROVIDER="${5:-github-provider}"
SA_EMAIL="${6:-speakaudio2-sa@${PROJECT_ID}.iam.gserviceaccount.com}"

gcloud config set project "$PROJECT_ID"

echo "==> Create Workload Identity Pool"
gcloud iam workload-identity-pools describe "$POOL" --location="global" >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools create "$POOL" --location="global" --display-name="GitHub Pool"

echo "==> Create Provider for GitHub OIDC"
gcloud iam workload-identity-pools providers describe "$PROVIDER" \
  --location="global" --workload-identity-pool="$POOL" >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
    --workload-identity-pool="$POOL" --location="global" \
    --display-name="GitHub Provider" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.actor=assertion.actor,attribute.ref=assertion.ref"

PROVIDER_RESOURCE=$(gcloud iam workload-identity-pools providers describe "$PROVIDER" \
  --location="global" --workload-identity-pool="$POOL" --format="value(name)")

echo "==> Allow repo ${GH_OWNER}/${GH_REPO} to impersonate ${SA_EMAIL}"
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${PROVIDER_RESOURCE}/attribute.repository/${GH_OWNER}/${GH_REPO}"

echo "==> Done"
cat <<EOF
WIF Provider resource:
${PROVIDER_RESOURCE}

Add these GitHub Action secrets:
- GCP_PROJECT=${PROJECT_ID}
- DEPLOY_SA=${SA_EMAIL}
- WIP=${PROVIDER_RESOURCE}
EOF
