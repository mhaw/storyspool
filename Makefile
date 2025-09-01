GCP_PROJECT ?= $(shell gcloud config get-value project 2>/dev/null)
ifeq ($(GCP_PROJECT),)
$(error GCP_PROJECT is not set. Please run `gcloud config set project <your-project-id>` or pass it as an argument: `make deploy-staging GCP_PROJECT=<your-project-id>`)
endif
SECRET_NAME := SPEAKAUDIO2_TASK_TOKEN
SA_EMAIL := speakaudio2-sa@$(GCP_PROJECT).iam.gserviceaccount.com

# StorySpool Makefile

# Default Python/venv
PYTHON := .venv/bin/python
PIP := .venv/bin/pip

# Variables for Cloud Run deployment
CLOUD_RUN_SERVICE = storyspool-staging
CLOUD_RUN_REGION = us-central1

# Project directories
VENV_DIR = .venv
APP_DIR = app
TEST_DIR = tests

# --- Config (override via env: make build-image PROJECT_ID=storyspool-be776) ---
PROJECT_ID ?= storyspool-be776
REGION ?= us-central1
# Artifact Registry location and repo (AR is recommended over Container Registry)
AR_LOCATION ?= us
AR_REPO ?= storyspool-staging
TAG := $(shell date +%Y%m%d-%H%M%S)
# Artifact Registry image path: <location>-docker.pkg.dev/<project>/<repo>/<image>:<tag>
IMAGE := $(AR_LOCATION)-docker.pkg.dev/$(PROJECT_ID)/$(AR_REPO)/storyspool-staging:$(TAG)

.PHONY: all clean install test lint format run build-image deploy-image deploy-staging logs print-vars FORCE test-fast check-env check-app dev css fmt check deploy-prod setup-secrets extract tts failed-build-logs

print-vars:
	@echo "PROJECT_ID=$(PROJECT_ID)"
	@echo "REGION=$(REGION)"
	@echo "AR_LOCATION=$(AR_LOCATION)"
	@echo "AR_REPO=$(AR_REPO)"
	@echo "TAG=$(TAG)"
	@echo "IMAGE=$(IMAGE)"

# Always run this target (prevents 'Nothing to be done')
FORCE:

# Run the Flask app locally
dev:
	FIREBASE_AUTH_EMULATOR_HOST=localhost:9099 FIRESTORE_EMULATOR_HOST=localhost:8080 $(PYTHON) -m flask run --host=0.0.0.0 --port=8081 --reload

# Tailwind watcher (assumes package.json script "dev:css")
css:
	npm run dev:css

# Install all dependencies
install:
	$(PIP) install -r requirements.txt
	npm install

# Run tests
test: install
	@echo "Running tests..."
	@$(VENV_DIR)/bin/pytest $(TEST_DIR)
	@echo "Tests finished."

test-fast: install
	@echo "Running fast tests..."
	@$(VENV_DIR)/bin/pytest -q --maxfail=1 tests/test_worker.py::test_run_job_success || exit 1
	@echo "Fast tests finished."

# Preflight Checks
check-env:
	@[ -n "$(GCP_PROJECT)" ] || (echo "[env] GOOGLE_CLOUD_PROJECT missing. Please set it." && exit 2)
	@[ -n "$(GCS_BUCKET)" ] || (echo "[env] GCS_BUCKET missing. Please set it." && exit 2)
	@echo "[env] All required environment variables are set."

check-app:
	@echo "[check] Verifying Gunicorn app import..."
	@$(PYTHON) -c 'import importlib, os, sys; mod = os.getenv("GUNICORN_APP","wsgi:app").split(":")[0]; print(f"[check] Importing {mod} ..."); importlib.import_module(mod); assert hasattr(sys.modules[mod], "app"); print("[check] OK")'
	@echo "[check] Flask/Gunicorn app import verified."

# Run linting/formatting checks
lint:
	pre-commit run --all-files

# Auto-format Python with black + isort
fmt:
	black .
	isort .

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + \
	find . -type f -name "*.pyc" -delete

# Combined check: format → lint → test
check: fmt lint test
	@echo "✅ All checks passed"



logs:
	gcloud run services logs read storyspool-staging --region $(REGION) --limit=200 --tail

build-image:
	gcloud builds submit --config cloudbuild.yaml \
		--substitutions=_IMAGE=$(IMAGE),_FIREBASE_PROJECT_ID=$(PROJECT_ID) .
	@echo "Docker image built: $(IMAGE)"

deploy-staging: build-image
	gcloud run deploy $(CLOUD_RUN_SERVICE) \
		--image $(IMAGE) \
		--region $(CLOUD_RUN_REGION) \
		--allow-unauthenticated # Assuming staging is publicly accessible for testing
	@echo "Staging deployment complete. Service: $(CLOUD_RUN_SERVICE), Region: $(CLOUD_RUN_REGION)"

deploy-prod:
	gcloud run deploy storyspool-prod \
		--source . \
		--region us-central1 \
		--service-account=speakaudio2-sa@$(GCP_PROJECT).iam.gserviceaccount.com \
		--allow-unauthenticated

# Setup Secret Manager secret and permissions
setup-secrets:
	@echo "Ensuring Secret Manager secret exists and permissions are set..."
	# Create secret if it doesn\'t exist (idempotent)
	gcloud secrets describe $(SECRET_NAME) --project=$(GCP_PROJECT) &>/dev/null || \
	gcloud secrets create $(SECRET_NAME) --project=$(GCP_PROJECT) --replication-policy="automatic"

	# Add secret version (prompts for value, idempotent - adds new version if value changes)
	@echo "Please paste the value for $(SECRET_NAME) and press Enter (will not be echoed):"
	@read -s SECRET_VALUE; \
	printf "$$SECRET_VALUE" | gcloud secrets versions add $(SECRET_NAME) --data-file=- --project=$(GCP_PROJECT)

	# Grant service account access to the secret (idempotent)
	gcloud secrets add-iam-policy-binding $(SECRET_NAME) \
		--member="serviceAccount:$(SA_EMAIL)" \
		--role="roles/secretmanager.secretAccessor" \
		--project=$(GCP_PROJECT)
	@echo "Secret setup complete."

extract:
	@echo "Extracting article from URL: $(URL)"
	@mkdir -p .cache
	@$(PYTHON) scripts/extract.py $(URL) > .cache/extracted_article.json
	@echo "Article data saved to .cache/extracted_article.json"


tts: .cache/extracted_article.json
	@echo "Synthesizing audio from .cache/extracted_article.json"
	@$(PYTHON) scripts/tts.py .cache/extracted_article.json

failed-build-logs:
	@echo "Fetching logs for the last failed build..."
	@./scripts/get_last_failed_build_log.sh
