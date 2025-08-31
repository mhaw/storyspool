# Dockerfile (minimal, working Python runtime for Cloud Run/local)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8081 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (if you need libsndfile/ffmpeg/etc., add here)
RUN apt-get update && apt-get install -y --no-install-recommends     ca-certificates curl ffmpeg &&     rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# App code
# Force rebuild of app code layer
COPY . .
RUN ls -lR /app

# (Optional) Tailwind build is skipped for now; you already ship compiled CSS in app/static/css
# Add it back later if needed with a guarded step.

# Simple healthcheck (Cloud Run also just needs the app to listen on $PORT)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD curl -fsS http://127.0.0.1:${PORT}/health || exit 1

# Gunicorn
CMD gunicorn 'wsgi:app' --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile -
