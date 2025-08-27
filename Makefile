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
test:
	pytest -q

# Run linting/formatting checks
lint:
	pre-commit run --all-files

# Auto-format Python with black + isort
fmt:
	black .
	isort .

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Combined check: format → lint → test
check: fmt lint test
	@echo "✅ All checks passed"

check-app:
	@echo "[check] Verifying Flask app import path..."
	@$(PYTHON) -c 'import importlib, os, sys; mod = os.getenv("GUNICORN_APP","wsgi:app").split(":")[0]; print(f"[check] Importing {mod} ..."); importlib.import_module(mod); assert hasattr(sys.modules[mod], "app"); print("[check] OK")'

# Build and deploy (requires gcloud + config in scripts/)
deploy-staging: check-app
	@echo "Building container image with Cloud Build..."
	gcloud builds submit . --config=cloudbuild.yaml --substitutions=_FIREBASE_PROJECT_ID=$(GCP_PROJECT)
	@echo "Deploying image to Cloud Run..."
	gcloud run deploy storyspool-staging \
		--image gcr.io/$(GCP_PROJECT)/storyspool-staging:latest \
		--region us-central1 \
		--service-account=speakaudio2-sa@$(GCP_PROJECT).iam.gserviceaccount.com \
		--allow-unauthenticated \
		--port 8080 \
		--cpu 1 \
		--memory 512Mi \
		--min-instances 0 \
		--max-instances 1 \
		--ingress all \
		--set-env-vars ENV=staging,FIRESTORE_COLLECTION=articles_staging,GCS_BUCKET=speakaudio2-audio-staging,TASKS_QUEUE=speakaudio2-jobs,TASKS_LOCATION=us-central1 \
		--set-secrets=TASK_TOKEN=SPEAKAUDIO2_TASK_TOKEN:latest


deploy-prod:
	gcloud run deploy storyspool-prod \
		--source . \
		--region us-central1 \
		--service-account=speakaudio2-sa@$(GCP_PROJECT).iam.gserviceaccount.com \
		--allow-unauthenticated

# Setup Secret Manager secret and permissions
setup-secrets:
	@echo "Ensuring Secret Manager secret exists and permissions are set..."
	# Create secret if it doesn't exist (idempotent)
	gcloud secrets describe $(SECRET_NAME) --project=$(GCP_PROJECT) &>/dev/null || \
	gcloud secrets create $(SECRET_NAME) --project=$(GCP_PROJECT) --replication-policy="automatic"

	# Add secret version (prompts for value, idempotent - adds new version if value changes)
	@echo "Please paste the value for $(SECRET_NAME) and press Enter (will not be echoed):"
	@read -s SECRET_VALUE; \
	printf "$SECRET_VALUE" | gcloud secrets versions add $(SECRET_NAME) --data-file=- --project=$(GCP_PROJECT)

	# Grant service account access to the secret (idempotent)
	gcloud secrets add-iam-policy-binding $(SECRET_NAME) \
		--member="serviceAccount:$(SA_EMAIL)" \
		--role="roles/secretmanager.secretAccessor" \
		--project=$(GCP_PROJECT)
	@echo "Secret setup complete."

.PHONY: extract tts

extract:
	@echo "Extracting article from URL: $(URL)"
	@mkdir -p .cache
	@$(PYTHON) scripts/extract.py $(URL) > .cache/extracted_article.json
	@echo "Article data saved to .cache/extracted_article.json"


tts: .cache/extracted_article.json
	@echo "Synthesizing audio from .cache/extracted_article.json"
	@$(PYTHON) scripts/tts.py .cache/extracted_article.json

.PHONY: failed-build-logs
failed-build-logs:
	@echo "Fetching logs for the last failed build..."
	@./scripts/get_last_failed_build_log.sh
