# StorySpool Architecture

This document outlines the high-level architecture of the StorySpool application.

## Overview

StorySpool is a web application designed to convert text into audio stories. It leverages a Flask backend for API services and a modern frontend for user interaction. Google Cloud Platform (GCP) services are used for various functionalities, including text-to-speech, queuing, and database.

## Components

### 1. Frontend

-   **Technology:** HTML, CSS (Tailwind CSS), JavaScript.
-   **Purpose:** Provides the user interface for creating, managing, and listening to stories. Handles user authentication via Firebase SDK.

### 2. Backend (Flask Application)

-   **Technology:** Python, Flask.
-   **Deployment:** Google Cloud Run.
-   **Purpose:**
    -   Serves the frontend static files.
    -   Exposes RESTful APIs for story management, user profiles, and initiating text-to-speech jobs.
    -   Interacts with various GCP services.

### 3. Google Cloud Platform (GCP) Services

-   **Firebase Authentication:** Manages user authentication and authorization.
-   **Firestore:** NoSQL document database for storing story metadata, user profiles, and job statuses.
-   **Cloud Tasks:** A fully managed asynchronous task queue used to trigger background text-to-speech processing.
-   **Cloud Text-to-Speech:** Converts text input into natural-sounding audio.
-   **Cloud Storage:** Stores the generated audio files.
-   **Cloud Run:** Serverless platform for deploying the Flask backend and potentially the worker.

### 4. Worker

-   **Technology:** Python, Flask (part of the main Flask app, triggered via Cloud Tasks).
-   **Purpose:**
    -   Receives tasks from Cloud Tasks (via the `/task/worker` endpoint).
    -   Orchestrates the text-to-speech process:
        -   Fetches story text from Firestore.
        -   Calls Cloud Text-to-Speech API.
        -   Uploads generated audio to Cloud Storage.
        -   Updates job status in Firestore.

## Data Flow

1.  **User Interaction:** A user creates a new story via the frontend.
2.  **Frontend to Backend:** The frontend sends a request to the Flask backend API to create a new story entry in Firestore.
3.  **Backend to Cloud Tasks:** The Flask backend creates a new task in Cloud Tasks, passing the `job_id` for the text-to-speech process.
4.  **Cloud Tasks to Worker:** Cloud Tasks dispatches the task to the `/task/worker` endpoint of the Flask application (which acts as the worker).
5.  **Worker to GCP Services:**
    -   The worker fetches story details from Firestore using the `job_id`.
    -   It sends the text to Cloud Text-to-Speech.
    -   It receives the audio data and uploads it to Cloud Storage.
    -   Finally, it updates the job status in Firestore.
6.  **Frontend Updates:** The frontend polls Firestore or uses real-time updates (if implemented) to reflect the story's processing status and eventually play the audio.

## Configuration

Environment variables are loaded from the `.env` file in the project root at application startup using `python-dotenv`. This allows for local development configuration without modifying the codebase.
