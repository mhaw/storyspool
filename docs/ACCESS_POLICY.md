# Access Policy for StorySpool Staging Testers

## Scope of Testers
Staging testers are granted temporary access to the StorySpool staging environment for the purpose of functional testing and dogfooding. Their access is limited to the staging project and specific roles as outlined below.

## Data Handling
- **Temporary Credentials:** Test account passwords are temporary. Testers are required to reset their passwords upon first login.
- **No PII in Test Articles:** Testers must ensure that no Personally Identifiable Information (PII) or sensitive data is submitted through the application, even in the staging environment. All test articles should use dummy or publicly available content.
- **Out-of-Band Password Distribution:** Initial temporary passwords will be distributed securely and out-of-band (e.g., not via Git or public issue trackers).

## Role and Permissions (Optional IAM)
If IAM roles are granted, testers will typically have:
- `roles/viewer`: For read-only access to the GCP Console for the staging project.
- `roles/logging.viewer`: For viewing logs related to the staging environment.
This access is for debugging and observation purposes only and does not grant modification rights.

## Rotation Cadence
Test account credentials and associated permissions should be reviewed and rotated periodically (e.g., monthly or after major testing cycles) to maintain security best practices.

---
