import os

from dotenv import load_dotenv

from app import create_app

# Only load .env locally (Cloud Run sets K_SERVICE)
if not os.getenv("K_SERVICE"):
    # Do not override existing env vars coming from the runtime
    load_dotenv(override=False)

app = create_app()
