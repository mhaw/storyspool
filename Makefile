PY=python
PIP=pip

.PHONY: dev css test fmt lint build docker-run deploy-staging deploy-prod

dev:
	$(PY) -m flask --app wsgi run -p 8080

css:
	npm run dev:css

test:
	pytest -q

fmt:
	black . && isort .

lint:
	flake8 .

build:
	docker build -t storyspool .

docker-run:
	docker run -p 8080:8080 --env-file .env -v $$HOME/.config/gcloud:/root/.config/gcloud storyspool

deploy-staging:
	gcloud builds submit --tag us-central1-docker.pkg.dev/$$GOOGLE_CLOUD_PROJECT/storyspool/app:$(shell git rev-parse --short HEAD)
	gcloud run deploy storyspool-staging --image us-central1-docker.pkg.dev/$$GOOGLE_CLOUD_PROJECT/storyspool/app:$(shell git rev-parse --short HEAD) --region us-central1 --allow-unauthenticated --service-account storyspool-sa@$$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com --set-env-vars ENV=staging

deploy-prod:
	gcloud builds submit --tag us-central1-docker.pkg.dev/$$GOOGLE_CLOUD_PROJECT/storyspool/app:$(shell git rev-parse --short HEAD)
	gcloud run deploy storyspool-prod --image us-central1-docker.pkg.dev/$$GOOGLE_CLOUD_PROJECT/storyspool/app:$(shell git rev-parse --short HEAD) --region us-central1 --allow-unauthenticated --service-account storyspool-sa@$$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com --set-env-vars ENV=prod
