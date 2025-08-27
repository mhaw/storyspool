import argparse
import json
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.extract import extract_article


def main():
    parser = argparse.ArgumentParser(description="Extract article content from a URL.")
    parser.add_argument("url", help="The URL of the article to extract.")
    args = parser.parse_args()

    article_data = extract_article(args.url)
    print(json.dumps(article_data, indent=2))


if __name__ == "__main__":
    main()
