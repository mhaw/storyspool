FROM python:3.13-slim@sha256:1d6131b5d479888b43200645e03a78443c7157efbdb730e6b48129740727c312 AS base
WORKDIR /app
# Pinning OS packages (e.g., build-essential, curl, nodejs, npm, ffmpeg, git, libsndfile1) by version
# is recommended for full reproducibility, but can be complex. Consider using a more specific
# base image or a tool like 'apt-get install <package>=<version>' if needed.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl nodejs npm ffmpeg git libsndfile1 jq && rm -rf /var/lib/apt/lists/*
COPY .firebaserc ./
RUN npm install -g firebase-tools
COPY package.json package-lock.json ./
RUN FIREBASE_PROJECT_ID=$(jq -r '.projects.default' .firebaserc) && \
    echo "FIREBASE_PROJECT_ID: ${FIREBASE_PROJECT_ID}" && \
    firebase dataconnect:sdk:generate --project ${FIREBASE_PROJECT_ID}
RUN npm cache clean --force && npm ci && npm rebuild
# Example of using BuildKit secrets (if needed for build-time sensitive data):
# RUN --mount=type=secret,id=mysecret cat /run/secrets/mysecret
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN npx tailwindcss -i app/static/css/input.css -o app/static/css/output.css --minify

FROM python:3.13-slim@sha256:1d6131b5d479888b43200645e03a78443c7157efbdb730e6b48129740727c312
WORKDIR /app
# Install only necessary runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN adduser --system --group appuser

# Copy only essential Python site-packages and binaries
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy application code
COPY --from=base /app /app
# Set permissions for the appuser
RUN chown -R appuser:appuser /app

USER appuser

ENV PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl --fail http://localhost:8080/healthz || exit 1
CMD ["gunicorn", "-b", "0.0.0.0:8080", "wsgi:app"]
