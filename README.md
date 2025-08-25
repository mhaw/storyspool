# StorySpool

Turn stories into podcasts you can spool up anytime.

## 5‑minute Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install
cp .env.example .env  # edit GCP_PROJECT, GCS_BUCKET, FIRESTORE_COLLECTION
gcloud auth application-default login
make dev  # and in another terminal: npm run dev:css
```
Then open http://localhost:8080, log in (Firebase web client to be added), paste a URL.

## Deploy (staging)
- Set envs in Cloud Run (see docs/SETUP_GCP.md), then:
- Push a PR to `develop` → CI auto‑deploys to **storyspool-staging**.
