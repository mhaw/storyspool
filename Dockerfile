# STAGE 1: Build Environment
FROM python:3.12-slim AS build
WORKDIR /app

# Install system-level dependencies that rarely change
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    nodejs \
    npm \
    ffmpeg \
    git \
    libsndfile1 \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to leverage caching
# This layer only rebuilds if requirements.txt changes
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies, generating the Data Connect SDK first
COPY package.json package-lock.json ./
COPY .firebaserc ./
ARG FIREBASE_PROJECT_ID

RUN test -n "$FIREBASE_PROJECT_ID" || (echo "Build failed: FIREBASE_PROJECT_ID is not set." && exit 1)
RUN npm install -g firebase-tools
RUN firebase dataconnect:sdk:generate --project="$FIREBASE_PROJECT_ID"
RUN mkdir -p dataconnect-generated/js/default-connector && \
    echo '{"name": "@firebasegen/default-connector", "version": "1.0.0", "main": "index.cjs.js"}' > dataconnect-generated/js/default-connector/package.json
RUN npm ci && npm rebuild

# Now, copy the rest of the application code
COPY . .

# Run build steps that depend on the full source code
RUN npx tailwindcss -i app/static/css/input.css -o app/static/css/output.css --minify


# STAGE 2: Final Production Image
FROM python:3.12-slim AS final
WORKDIR /app

# Install only necessary runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN adduser --system --group appuser

# Copy installed dependencies from the build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /app/node_modules /app/node_modules

# Copy application code and generated assets
COPY --from=build /app /app

# Set permissions for the appuser
RUN chown -R appuser:appuser /app

USER appuser

ENV PATH="/usr/local/bin:$PATH"

ENV PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:8080/health || exit 1
CMD ["gunicorn", "-w", "2", "-k", "gevent", "--bind", "0.0.0.0:8080", "wsgi:app"]
