import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import json

from app.services.extract import extract_article


def main():
    parser = argparse.ArgumentParser(description="Extract article content from a URL.")
    parser.add_argument("url", help="The URL of the article to extract.")
    args = parser.parse_args()

    article_data = extract_article(args.url)
    print(json.dumps(article_data, indent=2))


if __name__ == "__main__":
    main()
