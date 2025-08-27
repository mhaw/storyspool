# Changelog

## [Unreleased]

### Added

### Changed
- Problem: pytest tests failing due to SSML escaping and incorrect job status transition assertions.
- Contract Chosen: SSML uses raw double quotes (`"`). Job status transitions defined for success and failure paths.
- Minimal Changes: Fixed `app/services/tts.py` to produce raw double quotes. Updated `tests/test_tts.py` and `tests/test_worker.py` to align with the defined contracts. Added `make test-fast` and `pytest.ini` hardening.
- Improved `scripts/tts.py`: Implemented structured logging, granular error handling, robust input validation, simplified idempotency, and temporary file cleanup.

### Fixed

### Removed
