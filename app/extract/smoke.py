import argparse
import asyncio

from app.extract import \
    extract_pipeline  # Assuming extract_pipeline is exposed in __init__.py


async def main():
    parser = argparse.ArgumentParser(
        description="Smoke test for URL extraction pipeline."
    )
    parser.add_argument("--url", required=True, help="URL to extract.")
    args = parser.parse_args()

    print(f"Attempting to extract from: {args.url}")
    try:
        result = await extract_pipeline(args.url)
        print("\n--- Extraction Result ---")
        print(f"Canonical URL: {result.url_canonical}")
        print(f"Title: {result.title}")
        print(
            f"Text Excerpt: {result.text_excerpt[:200]}..."
            if result.text_excerpt
            else "N/A"
        )
        print(f"Status: {result.status}")
        if result.error_code:
            print(f"Error Code: {result.error_code}")
        print(f"Parser Used: {result.parser_name} v{result.parser_version}")
        print(f"Fetched At: {result.fetched_at}")
    except Exception as e:
        print(f"An error occurred during extraction: {e}")


if __name__ == "__main__":
    asyncio.run(main())
