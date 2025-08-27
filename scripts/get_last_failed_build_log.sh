#!/bin/bash
set -e
LAST_FAILED_BUILD_ID=$(gcloud builds list --filter='status="FAILURE"' --limit=1 --format="value(id)")
if [ -n "$LAST_FAILED_BUILD_ID" ]; then
  echo "Last failed build ID: $LAST_FAILED_BUILD_ID"
  gcloud builds log "$LAST_FAILED_BUILD_ID"
else
  echo "No failed builds found."
fi
