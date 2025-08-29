## MVP Deploy (3 steps)
1) Run critical tests: `make test-fast`
2) Build (optional local): `make build`
3) Deploy to staging: `make deploy-staging` and tail logs: `make logs`

For more detailed deployment information, refer to the Makefile targets.

### Artifact Registry Setup (required)
- Enable APIs:
  - `gcloud config set project storyspool-be776`
  - `gcloud services enable artifactregistry.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com`
- Create AR repo (one-time):
  - `gcloud artifacts repositories create storyspool-staging --repository-format=docker --location=us --description="Storyspool staging images"`
- Grant Cloud Build push rights:
  - `PROJECT_ID=storyspool-be776`
  - `PROJECT_NUMBER=417579885597`
  - `gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role=roles/artifactregistry.writer`
- Optional: Configure local Docker auth for AR:
  - `gcloud auth configure-docker us-docker.pkg.dev`

Makefile now builds/pushes to `$(AR_LOCATION)-docker.pkg.dev/$(PROJECT_ID)/$(AR_REPO)/storyspool-staging:$(TAG)`.

### One‑shot Setup Script
- Run the helper to automate API/IAM/repo setup:
  - `bash scripts/setup_gcp_permissions.sh --project storyspool-be776`
- Options:
  - `--location us` (default) or a regional location like `us-central1`
  - `--repo storyspool-staging` (default)
  - `--billing-account XXXX-XXXX-XXXX` to link billing (requires permissions)
  - `--also-container-registry` to enable CR and grant Storage Admin (fallback)
  - `--no-docker-auth` to skip local Docker auth configuration
