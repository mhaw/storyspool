# Changelog

## [Unreleased]

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
- Corrected the feed title generation in `app/routes.py` to match test assertions.
- Added `GCS_BUCKET_NAME` to the test configuration to prevent `KeyError` during integration tests.
