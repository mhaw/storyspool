# StorySpool

StorySpool is a web application that allows users to generate audio stories from text.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Features

- Text-to-speech generation
- Story management
- User authentication (Firebase)

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a detailed overview of the system architecture.

## Local Development

### Prerequisites

- Python 3.9+
- Node.js 16+
- Google Cloud SDK (gcloud CLI)
- Firebase CLI
- Docker (for local Firebase Emulator Suite)

### Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-org/storyspool.git
    cd storyspool
    ```

2.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Node.js dependencies:**

    ```bash
    npm install
    ```

4.  **Set up Firebase Emulators:**

    Ensure you have the Firebase CLI installed (`npm install -g firebase-tools`).
    Start the emulators:

    ```bash
    firebase emulators:start --import=./firebase-data --export-on-exit=./firebase-data
    ```

    This will start Firestore, Authentication, and Storage emulators. The `--import` and `--export-on-exit` flags ensure your local data persists across sessions.

5.  **Configure environment variables:**

    Create a `.env` file in the project root based on `.env.example`.
    At a minimum, you'll need:

    ```
    FLASK_APP=wsgi.py
    FLASK_ENV=development
    FIREBASE_PROJECT_ID=your-local-firebase-project-id # e.g., storyspool-dev
    # ... other variables from .env.example
    ```

    You can find your local Firebase project ID in the Firebase Emulator UI (usually `localhost:4000`).

6.  **Run database migrations (if any):**

    For Flask-Migrate or similar, if applicable. (Currently, Firestore is NoSQL, so no traditional migrations).

7.  **Run the development server:**

    ```bash
    make dev
    ```

    This will start the Flask development server and Tailwind CSS watcher. The application will be accessible at `http://127.0.0.1:8080`.

### Local Dev Notes

-   **Firebase Authentication:** When running locally with Firebase Emulators, you can create test users directly in the Firebase Emulator UI (Authentication tab).
-   **Tailwind CSS:** Changes to `app/static/css/input.css` will automatically recompile `app/static/css/output.css` due to the `npm run watch-css` command in `make dev`.
-   **Hot Reloading:** Flask's development server provides hot reloading for Python code changes.

### Local worker test

To test the `/task/worker` endpoint locally:

1.  Ensure your `.env` file (in the project root) contains `TASK_TOKEN=dev`. If you modify `.env`, you must restart the development server (`make dev`).
2.  Obtain a real `JOB_ID` from your local Firebase/Firestore setup (e.g., by creating a new job via the UI).
3.  Execute the following `curl` command, replacing `<REAL_JOB_ID>` with an actual job ID:

    ```bash
    curl -X POST http://127.0.0.1:8080/task/worker \
      -H "Content-Type: application/json" \
      -H "X-Task-Token: dev" \
      --data '{"job_id":"<REAL_JOB_ID>"}'
    ```
