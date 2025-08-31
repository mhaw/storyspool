# StorySpool
## 2-Minute MVP Test (Prod)
1. Ensure Cloud Run service has env vars set:
   - `APP_ENV=prod`
   - `PUBLIC_BASE_URL=https://<your-run-host>`
   - `FIREBASE_API_KEY`, `FIREBASE_PROJECT_ID`, `FIREBASE_AUTH_DOMAIN`, `FIREBASE_APP_ID`, `FIREBASE_MEASUREMENT_ID`
2. Visit the site and sign in with Google.
3. Submit a public article URL; wait for processing; play audio.

## Notes
- Firebase config is injected at render time; no hardcoded keys in templates.
- CSP is enforced in prod for Firebase + Google fonts/scripts.
- Static assets are cacheable in prod (long TTL).
