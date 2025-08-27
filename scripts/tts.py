import argparse
import hashlib
import json
import logging
import os
import shutil  # For cleaning up temp directories
import sys
import tempfile
from unittest.mock import patch  # Import patch

from app import create_app
from app.services import tts as tts_service  # Import tts module to patch its members
from app.services.tts import synthesize_article_to_mp3

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Synthesize audio from an article JSON file."
    )
    parser.add_argument(
        "json_file", help="The path to the JSON file containing article data."
    )
    args = parser.parse_args()

    article_data = {}
    try:
        with open(args.json_file, "r") as f:
            article_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Error: JSON file not found at {args.json_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Error: Invalid JSON in file {args.json_file}")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        url = article_data.get("url")
        text = article_data.get(
            "text"
        )  # Assuming 'text' is also a critical field for TTS

        if not url:
            logger.error("Error: JSON file must contain a 'url' key.")
            sys.exit(1)
        if not text:
            logger.warning(
                "Warning: 'text' key not found in JSON data. Synthesis might produce empty audio."
            )
            # sys.exit(1) # Not exiting, as synthesize_article_to_mp3 handles empty text

        urlhash = hashlib.sha1(url.encode("utf-8")).hexdigest()
        output_filename = f"{urlhash}.mp3"
        # Simplified idempotency: check if output file exists in current directory
        # A more robust solution would check GCS, but that's out of scope for this script's direct interaction.
        if os.path.exists(output_filename):
            logger.info(
                f"Audio file already exists locally: {output_filename}. Skipping synthesis."
            )
            sys.exit(0)

        temp_dir = None
        # Patch upload_audio_and_get_url for local testing
        # Patch app.services.tts.upload_audio_and_get_url because that's where it's imported and used by synthesize_article_to_mp3
        with patch(
            "app.services.tts.upload_audio_and_get_url",
            return_value="http://mock-gcs.com/mock_audio.mp3",
        ):
            try:
                output_path, gcs_url = synthesize_article_to_mp3(
                    article_data, urlhash=urlhash
                )
                logger.info(f"Audio file created at: {output_path}")
                logger.info(f"GCS URL: {gcs_url}")

                # Move the synthesized file to the current directory for easier access
                shutil.move(str(output_path), output_filename)
                logger.info(f"Moved synthesized audio to: {output_filename}")

            except Exception as e:
                logger.error(
                    f"An error occurred during audio synthesis: {e}", exc_info=True
                )
                sys.exit(1)
            finally:
                # Clean up the temporary directory created by synthesize_article_to_mp3
                # The output_path from synthesize_article_to_mp3 is a Path object,
                # its parent is the temporary directory.
                if "output_path" in locals() and output_path.parent.exists():
                    temp_dir = output_path.parent
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")


if __name__ == "__main__":
    main()
