FROM python:3.12-slim AS build
WORKDIR /app

# Enable non-free repository for fonts-ubuntu
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl nodejs npm ffmpeg git libsndfile1 jq \
    fonts-noto fonts-noto-color-emoji \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to leverage caching
# This layer only rebuilds if requirements.txt changes
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies
COPY package.json package-lock.json ./

# Generate Data Connect SDK (depends on .firebaserc and FIREBASE_PROJECT_ID)
# This step should ideally be cached.
COPY .firebaserc ./
ARG FIREBASE_PROJECT_ID
RUN test -n "$FIREBASE_PROJECT_ID" || (echo "Build failed: FIREBASE_PROJECT_ID is not set." && exit 1)
RUN npm install -g firebase-tools@13 # Pin firebase-tools to a stable major to avoid unexpected CLI changes
RUN firebase dataconnect:sdk:generate --project="$FIREBASE_PROJECT_ID"
RUN mkdir -p dataconnect-generated/js/default-connector &&     echo '{"name": "@firebasegen/default-connector", "version": "1.0.0", "main": "index.cjs.js"}' > dataconnect-generated/js/default-connector/package.json

# Now run npm ci to install all dependencies, including the generated file: dependency
RUN npm ci

# Build frontend assets (depends on input.css and tailwind.config.js)
# Copy only necessary files for this step
COPY app/static/css/input.css app/static/css/input.css
COPY tailwind.config.js ./
# Copy templates and static JS for TailwindCSS to scan
COPY app/templates/ ./app/templates/
COPY app/static/js/ ./app/static/js/
RUN npx tailwindcss -i app/static/css/input.css -o app/static/css/output.css --minify

# Now, copy the rest of the application code
# This should be the last COPY . . in the build stage
COPY . .


# STAGE 2: Final Production Image
FROM python:3.12-slim AS final
WORKDIR /app

# Install only necessary runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ffmpeg libsndfile1 poppler-utils libnss3 libfontconfig1 libgbm1 \
 && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN adduser --system --group appuser

# Copy installed dependencies from the build stage
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /app/node_modules /app/node_modules

# Copy application code and generated assets
COPY --from=build /app /app

# Set permissions for the appuser
RUN chown -R appuser:appuser /app

USER appuser

ARG FIREBASE_PROJECT_ID
ENV FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}
ENV PATH="/usr/local/bin:$PATH"

ENV PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:8080/health || exit 1
CMD ["sh", "-c", "exec gunicorn -w ${GUNICORN_WORKERS:-2} -k ${GUNICORN_WORKER_CLASS:-gevent} --bind 0.0.0.0:${PORT} ${GUNICORN_APP:-wsgi:app} --timeout ${GUNICORN_TIMEOUT:-120} --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT:-30}"]
