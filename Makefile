# StorySpool Makefile

# Default Python/venv
PYTHON := .venv/bin/python
PIP := .venv/bin/pip

# Run the Flask app locally
dev:
	$(PYTHON) -m flask run --host=0.0.0.0 --port=8080 --reload

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

# Build and deploy (requires gcloud + config in scripts/)
deploy-staging:
	gcloud run deploy storyspool-staging \
		--source . \
		--region us-central1 \
		--service-account=speakaudio2-sa@$(GCP_PROJECT).iam.gserviceaccount.com \
		--allow-unauthenticated \
		--port 8080 \
		--cpu 1 \
		--memory 512Mi \
		--min-instances 0 \
		--max-instances 1 \
		--ingress all \
		--health-check-path /healthz \
		--set-env-vars \
			ENV=staging,
			FIRESTORE_COLLECTION=articles_staging,
			GCS_BUCKET=speakaudio2-audio-staging,
			TASKS_QUEUE=speakaudio2-jobs,
			TASKS_LOCATION=us-central1 \
		--set-secrets=TASK_TOKEN=SPEAKAUDIO2_TASK_TOKEN:latest

deploy-prod:
	gcloud run deploy storyspool-prod \
		--source . \
		--region us-central1 \
		--service-account=speakaudio2-sa@$(GCP_PROJECT).iam.gserviceaccount.com \
		--allow-unauthenticated
