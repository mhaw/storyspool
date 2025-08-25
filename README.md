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

## Firebase Auth (local dev)

To enable client-side Firebase authentication for local development, follow these steps:

1.  **Go to Firebase Console:** Navigate to [https://console.firebase.google.com/](https://console.firebase.google.com/) and select or create your project.

2.  **Add a Web App:** In your Firebase project, add a new web app. You'll be given a `firebaseConfig` object. Copy this object.

3.  **Enable Google Sign-in Provider:**
    *   In the Firebase Console, go to "Authentication" -> "Sign-in method".
    *   Enable the "Google" provider.

4.  **Add Authorized Domains:**
    *   Still in "Authentication" -> "Sign-in method", scroll down to "Authorized domains".
    *   Add `localhost` and `127.0.0.1`. If you plan to deploy to Cloud Run, also add your Cloud Run service URLs (e.g., `your-service-xxxxxx-uc.a.run.app`).

5.  **Paste `firebaseConfig`:** Open `app/templates/base.html` and paste your copied `firebaseConfig` object into the `firebaseConfig` constant within the `<script>` tag.

6.  **Reload Application:** Reload your local StorySpool application in your browser. You should now see "Sign In" and "Sign Out" buttons in the header.
