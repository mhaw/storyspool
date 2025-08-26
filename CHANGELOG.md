## [Unreleased]
### Fixed
- **Build Failure:** Excluded `node_modules` and other artifacts from the git repository and Cloud Build source uploads by configuring `.gitignore` and `.gcloudignore`. This resolves build timeouts by significantly reducing the source bundle size.
### Added
- **CI Guardrail:** Added a check to the CI pipeline to fail the build if `node_modules` or `.venv` are ever committed.
- **Makefile Helper:** Added a `failed-build-logs` target to the `Makefile` to quickly fetch the last 200 lines of logs from a failed build for easier debugging.

## [Unreleased]
### Added
- Unit tests for the background job worker (`tests/test_worker.py`), covering both success and failure cases.
- Unit tests for the article extraction service (`tests/test_extract.py`), including happy path and fallback logic.
- Unit tests for the text-to-speech conversion service (`tests/test_tts.py`), covering synthesis and text chunking.
- Unit tests for the job management service (`tests/test_jobs.py`), covering job creation and existence checks.
- Unit tests for the data storage service (`tests/test_store.py`), covering article record saving, listing, and audio upload.
### Fixed
- Resolved local test environment failures by adding missing dependencies (`pytest`, `audioop-lts`) and configuring the test runner to correctly find the application module.
- Docker build failure: Ensured Firebase CLI can find the active project by copying `.firebaserc` into the Docker image.

## [Unreleased]
### Fixed
- Resolved "Working outside of application context" error by passing app config to Firebase Admin initialization.
- Ensured Firestore client is correctly initialized and available via app context.

## [Unreleased]
### Fixed
- Fixed "aud" mismatch by aligning Firebase Admin SDK project ID with client configuration and handling emulator mode tolerance.
- Fixed Firestore client initialization; eliminated `NoneType.collection` crashes by storing client in app context.
### Added
- New helper module `app/firebase_admin_ext.py` for Firebase Admin SDK initialization.
- Focused tests for Firestore client wiring (`tests/test_store.py`) and token verification behavior (`tests/test_users.py`).

## [0.1.7] - 2025-08-25
### Fixed
- Corrected `FIREBASE_PROJECT_ID` in `.env` to match the Firebase emulator's project ID (`storyspool-be776`).

## [0.1.0] - 2025-08-25
### Added
- Initial implementation of text-to-speech generation from URLs.
- Display of job status and playable audio on the home page.
### Fixed
- Resolved `audioop` dependency issue preventing TTS synthesis.

# Changelog

## [1.2.0] - 2025-08-25
### Added
- Initial implementation of the URL extraction pipeline (`app/extract/`).
- Integrated `trafilatura` for primary content extraction and `httpx` for fetching.
- Implemented URL canonicalization, fetching, parsing, and persistence (placeholder).
- Defined `ExtractedDocument` data contract and error handling.
- Introduced a manual smoke test script (`app/extract/smoke.py`).

## [1.1.0] - 2025-08-24

### Added

*   **Build Reliability:** Pinned base image digests (`python:3.11-slim@sha256:1d6131b5d479888b43200645e03a78443c7157efbdb730e6b48129740727c312`) in `Dockerfile` for deterministic builds.
*   **Security:** Implemented non-root user (`appuser`) execution in Docker containers to reduce attack surface.
*   **CI/CD:** Integrated SBOM generation (Syft) and vulnerability scanning (Trivy) into the CI pipeline (`deploy.yml`).
*   **CI/CD:** Enabled BuildKit remote caching for faster Docker image builds in CI (`deploy.yml`).
*   **Reliability:** Added `HEALTHCHECK` instruction to `Dockerfile` for improved container health monitoring.
*   **Observability:** Integrated structured logging (`python-json-logger`) for application logs.
*   **CI/CD:** Added placeholder for Cloud Run rollback strategy in `deploy.yml`.

### Changed

*   **CI/CD:** Enforced strict test success in `ci.yml` by removing `|| true` from `pytest` command.
*   **Dockerfile:** Optimized final stage Python artifact copying to reduce image size.
*   **Dockerfile:** Added `libsndfile1` to `apt-get install` to resolve `pydub`/`audioop` dependency.
*   **Application:** Re-enabled `pydub` functionality in `app/services/tts.py` for audio processing.
*   **Application:** Removed temporary `X-Task-Token` logging in `app/routes.py` in favor of structured logging.
*   **Dockerfile:** Added comment about BuildKit secrets usage.

### Fixed

*   **Core Functionality:** Resolved `pydub` / `audioop` dependency issue, enabling full Text-to-Speech functionality.
