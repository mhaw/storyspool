# Dockerfile (minimal, working Python runtime for Cloud Run/local)

# --- Build Stage ---
FROM python:3.12-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends curl ffmpeg && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# --- Final Stage ---
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8081 \
    GUNICORN_WORKERS=2 \
    GUNICORN_THREADS=4 \
    GUNICORN_TIMEOUT=120

WORKDIR /app

# Create a non-root user
RUN useradd --create-home appuser

# Copy system deps from builder
COPY --from=builder /usr/bin/ffmpeg /usr/bin/ffmpeg
COPY --from=builder /usr/bin/curl /usr/bin/curl

# Copy python deps from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy app code
COPY . .

# Change ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Simple healthcheck (Cloud Run also just needs the app to listen on $PORT)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD curl -fsS http://127.0.0.1:${PORT}/health || exit 1

# Gunicorn
CMD gunicorn 'wsgi:app' --bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} --access-logfile - --error-logfile -
