from dotenv import load_dotenv

from app import create_app

load_dotenv()  # Load environment variables from .env

app = create_app()
