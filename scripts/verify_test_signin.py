#!/usr/bin/env python3
import csv
import os
import sys

import requests

API_KEY = os.environ["FIREBASE_WEB_API_KEY"]


def signin(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    r = requests.post(
        url,
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["idToken"]


def main():
    ok, fail = 0, 0
    with open("secrets/test_accounts.out.csv") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        try:
            token = signin(row["email"], row["password"])
            print(f"[PASS] {row['email']} signed in; token len={len(token)}")
            ok += 1
        except Exception as e:
            print(f"[FAIL] {row['email']}: {e}")
            fail += 1
    print(f"RESULT: {ok} pass, {fail} fail")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
