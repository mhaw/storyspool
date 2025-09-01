#!/usr/bin/env python3
import csv
import os
import sys
from pathlib import Path

# Admin SDK
import firebase_admin
from firebase_admin import auth, credentials

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
API_KEY = os.environ.get("FIREBASE_WEB_API_KEY")
AUTH_DOMAIN = os.environ.get("AUTH_DOMAIN")
TEST_USERS_PATH = os.environ.get("TEST_USERS_PATH", "secrets/test_accounts.csv")
OPTIONAL_IAM = os.environ.get("OPTIONAL_IAM", "false").lower() == "true"


def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})


def load_users():
    # CSV schema: email,password
    users = []
    with open(TEST_USERS_PATH, newline="") as f:
        for row in csv.DictReader(f):
            users.append(
                {"email": row["email"].strip(), "password": row["password"].strip()}
            )
    return users


def ensure_user(u):
    try:
        rec = auth.get_user_by_email(u["email"])
        need_pw = False
    except auth.UserNotFoundError:
        rec = auth.create_user(
            email=u["email"],
            password=u["password"],
            email_verified=True,
            disabled=False,
        )
        need_pw = True
    # Set/merge claims
    claims = rec.custom_claims or {}
    claims.update({"tester": True, "env": "staging"})
    auth.set_custom_user_claims(rec.uid, claims)
    return rec, need_pw


def main():
    assert PROJECT_ID and API_KEY and AUTH_DOMAIN, "Missing required env vars."
    init_firebase()
    users = load_users()
    out_rows = []
    for u in users:
        rec, created = ensure_user(u)
        out_rows.append(
            {
                "email": u["email"],
                "password": u["password"],
                "uid": rec.uid,
                "created": created,
            }
        )
        print(f"[OK] {u['email']} -> {rec.uid} (created={created})")
    # Write normalized CSV with UIDs (overwrites input)
    out_path = Path("secrets/test_accounts.out.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["email", "password", "uid", "created"])
        w.writeheader()
        w.writerows(out_rows)
    print(f"[ARTIFACT] {out_path}")


if __name__ == "__main__":
    sys.exit(main())
