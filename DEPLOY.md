# StorySpool Deployment Log

## Staging Environment

### Deployment: 2025-08-31 (UTC)

*   **Service:** `storyspool-staging`
*   **Region:** `us-central1`
*   **Revision ID:** `storyspool-staging-00001-vvf`
*   **Service URL:** `https://storyspool-staging-417579885597.us-central1.run.app`
*   **Changes:** Implemented user article submission and feed integration. Includes new `/submit_article` route, Firestore integration, and RSS updates.
*   **Health Check (`/health`):** `ok`

---

## Staging Deployment Notes

**Date:** 2025-08-31
**Service:** `storyspool-staging`
**URL:** `https://storyspool-staging-417579885597.us-central1.run.app`
**Revision ID:** `storyspool-staging-00003-kz4`
**Image Tag:** `us-docker.pkg.dev/storyspool-be776/storyspool-staging/storyspool-staging:20250831-234658`

**Environment Variables Set:**
*   `FIREBASE_API_KEY`: AIzaSyAgWw6PAqcJUFolPDWVYcKxKRP7IwiYLko
*   `FIREBASE_AUTH_DOMAIN`: storyspool-be776.firebaseapp.com
*   `FIREBASE_PROJECT_ID`: storyspool-be776
*   `FIREBASE_APP_ID`: 1:417579885597:web:af29447d245af4f7c9d2f4
*   `FIREBASE_MEASUREMENT_ID`: G-FYE0G370KM
*   `GOOGLE_CLOUD_PROJECT`: storyspool-be776
*   `PUBLIC_BASE_URL`: https://storyspool-staging-417579885597.us-central1.run.app

**Health Check:** Passed (HTTP 200 OK)
