# Changelog

### Unreleased — Deployment stabilization
- Canonicalized Dockerfile (renamed Dockerfile.ctx → Dockerfile; removed legacy Dockerfile).
- Standardized project ID to `storyspool` across .firebaserc, .env.example, and code.
- Stopped DataConnect codegen during Docker build; committed/used generated SDK if present.
- Hardened Tailwind/JS build to be optional and reproducible.
- Firebase Admin initialization uses ADC on Cloud Run with env fallback.

## [Unreleased]
### Fixed
- Resolved Cloud Run service startup failures by:
  - Excluding `.env` from Docker image via `.dockerignore`.
  - Guarding `load_dotenv()` in `wsgi.py` to prevent overriding Cloud Run environment variables.
  - Updating `app/config.py` for robust environment variable loading.
  - Building Docker image for `linux/amd64` platform.
  - Explicitly setting all required environment variables during deployment.
- Hardened Cloud Run runtime service account:
  - Created `storyspool-runner` service account with least-privilege roles (`roles/datastore.user`, `roles/storage.objectAdmin`, `roles/secretmanager.secretAccessor`, `roles/logging.logWriter`, `roles/monitoring.metricWriter`).
  - Switched Cloud Run service to use `storyspool-runner`.
  - Removed overly broad `roles/editor` from default Compute Engine service account.
- Normalized Cloud Run service configuration:
  - Cleared diagnostic command/args overrides.
  - Set reliability knobs (`min-instances`, `max-instances`, `concurrency`, `cpu`, `memory`, `timeout`).


### Added
- **Podcast RSS Feed Generation**: Implemented a robust, on-demand RSS 2.0 feed generation service with proper iTunes and Atom namespaces for podcast compatibility (`app/services/rss.py`).
- **RSS Feed Endpoint**: Created a new endpoint at `/u/<uid>/feed.xml` to serve the personalized podcast feed with a 5-minute cache header (`app/routes.py`).
- **Comprehensive RSS Testing**: Added both unit tests (`tests/test_rss.py`) to validate XML structure and an integration test (`tests/test_rss_integration.py`) to verify the entire feed generation pipeline.
- **Personalized Article Page**: The main view for logged-in users is now a dedicated "My Articles" page, showing only their submitted content.
- **RSS Feed Discovery**: Added a prominent "Get My Podcast Feed" button on the articles page, which opens a modal with the user's unique RSS feed URL and a copy-to-clipboard feature.
- **Responsive UI**: The article list is now a responsive table that adapts to a card-like view on mobile devices for better usability.
- **Action Hierarchy**: Redesigned article actions with a primary "Listen" button and a dropdown for secondary actions ("Download MP3," "View Original") to declutter the UI.
- **Landing Page**: A new simple landing page is shown to anonymous users.
- Added tests for new routing and UI features.

### Changed
- **Test Fixtures**: Added standard Flask `app` and `client` fixtures to `tests/conftest.py` to support integration testing.
- **Improved Worker Error Handling**: The background worker now sets more granular error statuses (e.g., `failed_parse`, `failed_tts`) instead of a generic `failed_fetch` status, providing better feedback to the user.
- Renamed `index.html` template to `articles.html` to better reflect its purpose.
- The root route `/` now shows a landing page for anonymous users and redirects to `/articles` for authenticated users.

### Fixed
- **Test Suite**: Fixed multiple issues in the test suite, including a `ValueError` related to Firebase app initialization and several `AttributeError` and `AssertionError` exceptions in the routes tests.
- **Firestore Rules**: Updated Firestore security rules to require authentication for all read and write operations.
- **IAM Permissions**: Replaced the `roles/storage.objectAdmin` role with the more restrictive `roles/storage.objectCreator` and `roles/storage.objectViewer` roles in the `gcp_bootstrap.sh` script.
- **Configuration**: Replaced the hardcoded project ID in `.firebaserc` with a placeholder to allow for dynamic configuration.

### Fixed
- Corrected the feed title generation in `app/routes.py` to match test assertions.
- Added `GCS_BUCKET_NAME` to the test configuration to prevent `KeyError` during integration tests.

## [Unreleased]
### Fixed
- Unblocked container startup by using ADC (Option B) and reverting Firebase Admin init to Application Default credentials.

### Ops
- Documented local run with `GOOGLE_APPLICATION_CREDENTIALS` mount and explicit `GOOGLE_CLOUD_PROJECT`.
### Fixed
- Unblocked container startup by using ADC (Option B) and reverting Firebase Admin init to Application Default credentials.

### Ops
- Documented local run with `GOOGLE_APPLICATION_CREDENTIALS` mount and explicit `GOOGLE_CLOUD_PROJECT`.
- fix(auth): remove hardcoded Firebase config; inject from env.
- feat(security): enable CSP via Flask-Talisman in prod with Firebase/CDN allowlist.
- feat(static): long-cache static assets in prod.
- chore(proxy): add ProxyFix and sane cookie settings per env.
- docs: add 2-minute MVP test instructions.
- note(ci): prior Cloud Build failures observed on 2025-08-28 (investigate later).
- **Discrepancy:** `APP_ENV` and `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, `FIREBASE_APP_ID`, `FIREBASE_MEASUREMENT_ID` environment variables are not explicitly set in Cloud Run.
