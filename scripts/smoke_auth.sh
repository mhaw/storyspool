#!/usr/bin/env bash
set -euo pipefail
STAGING_URL="${STAGING_URL:?set STAGING_URL}"
API_KEY="${FIREBASE_WEB_API_KEY:?set FIREBASE_WEB_API_KEY}"
EMAIL="${TEST_EMAIL:?set TEST_EMAIL}"
PASS="${TEST_PASS:?set TEST_PASS}"

echo "→ Sign in with password to get ID token"
IDTOKEN=$(curl -s "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"returnSecureToken\":true}" | \
  python -c 'import sys,json;print(json.load(sys.stdin)["idToken"])')

echo "→ Exchange for session cookie"
curl -si -c cookies.txt -X POST "$STAGING_URL/sessionLogin" \
  -H 'Content-Type: application/json' \
  --data "{\"idToken\":\"$IDTOKEN\"}" | sed -n '1,12p'

echo "→ /articles (expect 200)"
curl -si -b cookies.txt "$STAGING_URL/articles" | sed -n '1,12p'

echo "→ Submit article (expect 200/302)"
curl -si -b cookies.txt -X POST "$STAGING_URL/submit_article" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "article_url=https://example.com/test-article-$(date +%s)" | sed -n '1,12p'

echo "✓ Smoke done"
