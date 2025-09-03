# Deployment Guide

This document outlines the process for deploying the StorySpool application to the staging and production environments.

## Environments

- **Staging (`storyspool-staging`):** A production-like environment for testing and verifying new features before they go live. This environment should be used for all integration testing and final verification.
- **Production (`storyspool-mvp`):** The live environment that serves end-users.

## Deployment Workflow

The standard workflow for deploying changes is as follows:

1.  **Develop Locally:** All new features and bug fixes should be developed and tested on your local machine first.
2.  **Push to `main`:** Once changes are complete and tested locally, push them to the `main` branch on GitHub.
3.  **Deploy to Staging:** Deploy the latest code from the `main` branch to the staging environment using the following command:
    ```bash
    make deploy-staging
    ```
4.  **Verify on Staging:** Thoroughly test the deployed changes on the staging URL (`https://storyspool-staging-417579885597.us-central1.run.app`). This includes:
    -   Performing a hard refresh (Cmd+Shift+R or Ctrl+Shift+R) to avoid browser cache issues.
    -   Checking for any console errors.
    -   Testing the core functionality of the application.
5.  **Deploy to Production:** Once the changes have been verified on staging, deploy them to the production environment.
    *Note: A `deploy-prod` target does not currently exist in the `Makefile`. You can create one based on the `deploy-staging` target, or run the `gcloud run deploy` command manually, ensuring you target the `storyspool-mvp` service.*

    Example command to create a `deploy-prod` target in your `Makefile`:
    ```makefile
    deploy-prod:
    	gcloud run deploy storyspool-mvp \
    		--image us-docker.pkg.dev/$(PROJECT_ID)/$(AR_REPO)/storyspool-staging:$(TAG) \
    		--region $(REGION) \
    		--allow-unauthenticated
    ```

This structured approach ensures that all changes are tested in a safe environment before being released to users, which helps maintain a stable and reliable service.
