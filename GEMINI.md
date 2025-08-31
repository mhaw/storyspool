# Gemini CLI Playbook

## Diagnose & Patch Template
Act as a senior Flask/GCP engineer on StorySpool.
Read: docs/ARCHITECTURE.md, app/services/tts.py, app/worker.py.
Task: <describe>
Output:
1) Exact shell commands to diagnose
2) A single unified diff (patch)
3) How to verify locally + in Cloud Run
Constraints: keep changes minimal; add logging at network boundaries.

---

## Gemini Added Memories
- The user wants to add test account login instructions to the README.md file. I need to ask the user for the test account credentials.
- The user prioritizes getting the project to a working state, even if it means temporarily disabling features or acknowledging failing tests. The user values keeping testing infrastructure (like pyproject.toml and Makefile) even if tests are not yet passing. Playwright installation can be problematic in local environments; suggest using Docker for development or specific installation guides. Flask-Talisman enforces HTTPS, which can cause issues in local HTTP-only development setups.
- Playbook for StorySpool Cloud Run startup failures:
1. **Role**: Flask/GCP/Firebase troubleshooter.
2. **Symptoms**: `[bash,...]: not found` (bad CMD JSON), `gunicorn: not found`, `bash: not found`, port binding errors.
3. **Goal**: Diagnose, provide unified diffs to fix, and harden the build.
4. **Process**:
    a. **Triage**: Get `Dockerfile`, `grep` for Flask app object (`wsgi:app`?), `grep` `requirements.txt` for `gunicorn`.
    b. **Diagnose**: Match symptoms to common causes (bad CMD form, missing package, wrong path).
    c. **Fix**: Provide diffs. Prefer `CMD ["gunicorn", ...]` (JSON exec form). Ensure `gunicorn` is in `requirements.txt`. Add a `/health` route to `app/routes.py`.
    d. **Verify**: Provide `docker build/run` and `gcloud run deploy` commands.
    e. **Harden**: Suggest `Makefile` pre-flight checks and configurable gunicorn env vars.
5. **Output**: Triage summary, root causes, diffs, verification/hardening steps, and a CHANGELOG entry.

---

## Gemini CLI Instructions (MVP Speed)

### 1) Pick fastest path & get /health green (single-shot)

ROLE: Pragmatic DevOps focused on MVP.
CONTEXT:
- App: StorySpool (Flask + Gunicorn; Firebase Auth + Firestore; optional GCS).
- Image: storyspool:local
- Observed: container runs but health check is stuck; previous crash due to missing FIREBASE_PROJECT_ID now fixed; logs may be empty.
- Two paths to config:
  A) Use local emulators (fast dev): FIRESTORE_EMULATOR_HOST, FIREBASE_AUTH_EMULATOR_HOST via host.docker.internal.
  B) Use real GCP creds (slower): mount ADC, set GOOGLE_APPLICATION_CREDENTIALS.
MISSION:
- Choose the **fastest** path to a successful `200 OK` from `http://localhost:8081/health`.
- Prefer A) emulators unless clearly unavailable.
- Do ONLY what’s necessary for MVP; skip polish.

DELIVERABLES:
1) State the chosen path (A or B) and a one-sentence reason.
2) Output ONE exact `docker run` command to start healthy (include envs, `--add-host=host.docker.internal:host-gateway`, bind 8081, and force Gunicorn to log to stdout with `GUNICORN_CMD_ARGS="--bind 0.0.0.0:8081 --workers 1 --threads 4 --timeout 60 --graceful-timeout 30 --access-logfile - --error-logfile - --log-level debug"`).
3) Provide ONE verification command: `curl -i http://localhost:8081/health` and the expected response snippet.
4) (Optional) If emulators are not reachable, automatically fall back to B and show the alternative `docker run` command that mounts ADC at `/secrets/adc.json` and sets `GOOGLE_APPLICATION_CREDENTIALS`.
5) List max THREE “fix later” items.

CONSTRAINTS:
- No refactors, no new files, no best-practice detours.
- Keep output concise and copy-pastable.

### 2) If /health still stuck → inspect health + events quickly

ROLE: Triage engineer.
GOAL: Determine why `/health` probe is stuck within 60 seconds.

OUTPUT: Copy-paste shell block(s) ONLY, with minimal comments.

COMMANDS TO RUN:
1) List containers:
   docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

2) Set NAME and inspect health:
   NAME=storyspool_local
   docker inspect "$NAME" --format '{{json .State.Health}}' | jq .
   docker inspect "$NAME" --format 'RestartCount={{.RestartCount}}  Status={{.State.Status}}  Health={{.State.Health.Status}}'

3) Check recent events (no --until now bug):
   docker events --since 5m --filter "container=$NAME" | sed -n '1,120p'

4) Probe from inside (verifies server & health path):
   docker exec -it "$NAME" sh -lc 'which curl || which wget || true; curl -sS http://127.0.0.1:8081/health || wget -qO- http://127.0.0.1:8081/health || echo PROBE_FAILED'

EXPECTED:
- `.State.Health.Status` becomes "healthy" OR event logs show repeated failing probes.
- If PROBE_FAILED and no logs, proceed to “Gunicorn verbose” prompt next.

### 3) Ensure healthcheck works even if curl/wget missing (MVP patch)

ROLE: Container surgeon.
GOAL: Make HEALTHCHECK succeed without installing extra packages.

ACTION:
- Replace the Dockerfile HEALTHCHECK with a Python-based probe that uses stdlib only.

PATCH (show as Dockerfile snippet to append to FINAL stage):
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python - <<'PY' || exit 1
import urllib.request, sys
try:
    with urllib.request.urlopen("http://127.0.0.1:8081/health", timeout=3) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
PY

AFTER:
- Rebuild & relaunch (reuse existing envs):
  docker build -t storyspool:local .
  && docker rm -f storyspool_local 2>/dev/null || true \
  && docker run --name storyspool_local -p 8081:8081 \
       --add-host=host.docker.internal:host-gateway \
       -e PORT=8081 \
       -e FIREBASE_PROJECT_ID=storyspool \
       -e GOOGLE_CLOUD_PROJECT=storyspool \
       -e GCLOUD_PROJECT=storyspool \
       -e FIRESTORE_EMULATOR_HOST=host.docker.internal:8080 \
       -e FIREBASE_AUTH_EMULATOR_HOST=host.docker.internal:9099 \
       -e GUNICORN_CMD_ARGS="--bind 0.0.0.0:8081 --workers 1 --threads 4 --timeout 60 --graceful-timeout 30 --access-logfile - --error-logfile - --log-level debug" \
       storyspool:local

VERIFY:
  docker inspect storyspool_local --format '{{json .State.Health}}' | jq .
  curl -i http://localhost:8081/health

### 4) Force Gunicorn to actually log (when docker logs is empty)

ROLE: Runtime fixer.
GOAL: See real server logs to debug quickly.

RUN:
docker rm -f storyspool_local 2>/dev/null || true
docker run --name storyspool_local \
  -p 8081:8081 \
  --add-host=host.docker.internal:host-gateway \
  -e PORT=8081 \
  -e FIREBASE_PROJECT_ID=storyspool \
  -e GOOGLE_CLOUD_PROJECT=storyspool \
  -e GCLOUD_PROJECT=storyspool \
  -e FIRESTORE_EMULATOR_HOST=host.docker.internal:8080 \
  -e FIREBASE_AUTH_EMULATOR_HOST=host.docker.internal:9099 \
  -e GUNICORN_CMD_ARGS="--bind 0.0.0.0:8081 --workers 1 --threads 4 --timeout 60 --graceful-timeout 30 --access-logfile - --error-logfile - --log-level debug" \
  storyspool:local
docker logs -f storyspool_local

IF NO REQUEST LOGS:
- Hit the endpoint:
  curl -i http://localhost:8081/health
EXPECT:
- Access log lines and 200 OK; otherwise error log reveals the next minimal fix.

### 5) One-liner fallback to real creds (when emulators aren’t available)

ROLE: Expedite MVP when emulators are down.
PREREQ: You have ADC at $HOME/.config/gcloud/application_default_credentials.json

RUN:
ADC="$HOME/.config/gcloud/application_default_credentials.json"
docker rm -f storyspool_local 2>/dev/null || true
docker run --name storyspool_local \
  -p 8081:8081 \
  -e PORT=8081 \
  -e FIREBASE_PROJECT_ID=storyspool \
  -e GOOGLE_CLOUD_PROJECT=storyspool \
  -e GCLOUD_PROJECT=storyspool \
  -v "$ADC":/secrets/adc.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/adc.json \
  -e GUNICORN_CMD_ARGS="--bind 0.0.0.0:8081 --workers 1 --threads 4 --timeout 60 --graceful-timeout 30 --access-logfile - --error-logfile - --log-level debug" \
  storyspool:local

VERIFY:curl -i http://localhost:8081/health

### 6) Post-success doc touch (CHANGELOG + .env.example) — optional after MVP

ROLE: Minimal doc update after green health.

TASKS:
1) Append to CHANGELOG.md:
## [Unreleased]
### Fixed
- Unblocked container startup by using ADC (Option B) and reverting Firebase Admin init to Application Default credentials.

### Ops
- Documented local run with `GOOGLE_APPLICATION_CREDENTIALS` mount and explicit `GOOGLE_CLOUD_PROJECT`.

2) Create .env.example with only required keys:
FIREBASE_PROJECT_ID=storyspool
GOOGLE_CLOUD_PROJECT=storyspool
GCLOUD_PROJECT=storyspool
# One of:
FIRESTORE_EMULATOR_HOST=localhost:8080
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
# or:
GOOGLE_APPLICATION_CREDENTIALS=/secrets/adc.json
PORT=8081
