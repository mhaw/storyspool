# StorySpool

## MVP Scope Definition
The core MVP for StorySpool is defined as:
- **Sign In:** Users can successfully authenticate via Google Sign-In.
- **Submit Article:** Users can submit a public article URL for processing.
- **See Article in Feed:** Processed articles appear in the user's personalized podcast feed.

All other features or enhancements are considered part of the "Polish Backlog" and will be addressed in subsequent iterations.
## 2-Minute MVP Test (Prod)
1. Ensure Cloud Run service has env vars set:
   - `APP_ENV=prod`
   - `PUBLIC_BASE_URL=https://<your-run-host>`
   - `FIREBASE_API_KEY`, `FIREBASE_PROJECT_ID`, `FIREBASE_AUTH_DOMAIN`, `FIREBASE_APP_ID`, `FIREBASE_MEASUREMENT_ID`
2. Visit the site and sign in with Google.
3. Submit a public article URL; wait for processing; play audio.

## Test Account Login
Use Google Sign-In with any Google account.

## Login Smoke Test (Browser)
1. Open your deployed Cloud Run URL: `https://storyspool-pqdggjhgsq-uc.a.run.app`
2. Open browser DevTools (F12) -> Console and Network tabs.
3. Click "Sign in with Google".
4. **Expected:** Redirect to Google login, then back to your app.
5. **Verify:**
   - No CSP errors in Console.
   - No failed network requests (red entries) related to Firebase or Google APIs.
   - A session cookie is set for your domain (check Application -> Storage -> Cookies).
   - The UI updates to show you are signed in.

## Notes
- Firebase config is injected at render time; no hardcoded keys in templates.
- CSP is enforced in prod for Firebase + Google fonts/scripts.
- Static assets are cacheable in prod (long TTL).
