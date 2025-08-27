import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import hashlib
import json

from app import create_app
from app.services.tts import synthesize_article_to_mp3


def main():
    parser = argparse.ArgumentParser(
        description="Synthesize audio from an article JSON file."
    )
    parser.add_argument(
        "json_file", help="The path to the JSON file containing article data."
    )
    args = parser.parse_args()

    with open(args.json_file, "r") as f:
        article_data = json.load(f)

    app = create_app()
    with app.app_context():
        url = article_data.get("url")
        if not url:
            print("Error: JSON file must contain a 'url' key.")
            sys.exit(1)

        urlhash = hashlib.sha1(url.encode("utf-8")).hexdigest()
        output_path, gcs_url = synthesize_article_to_mp3(article_data, urlhash=urlhash)
        print(f"Audio file created at: {output_path}")
        print(f"GCS URL: {gcs_url}")


if __name__ == "__main__":
    main()
