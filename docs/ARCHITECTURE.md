# StorySpool Architecture (MVP)

Flow: POST /jobs → Cloud Tasks → /task/worker → extract → SSML TTS → GCS → Firestore → per‑user RSS.

- App: Flask on Cloud Run (:8080), /healthz
- Queue: Cloud Tasks (2 retries)
- Data: Firestore (articles*), GCS (audio), urlhash idempotency
- Auth: Firebase ID tokens (admin via env allow-list)
- Observability: JSON logs with timings, request_id, job_id
