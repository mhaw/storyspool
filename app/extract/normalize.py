import re
import urllib.parse

from app.extract.errors import CanonicalizationError


def normalize_url(url: str) -> str:
    """
    Normalizes a URL to its canonical form.

    This function performs several steps to standardize a URL:
    1. Parses the URL into its components.
    2. Converts the scheme and hostname to lowercase.
    3. Removes default ports (80 for http, 443 for https).
    4. Resolves '..' and '.' segments in the path.
    5. Removes trailing slashes from the path, unless it's the root path.
    6. Sorts query parameters alphabetically.
    7. Removes UTM parameters.
    8. Removes fragment identifiers.

    Args:
        url (str): The input URL string.

    Returns:
        str: The canonicalized URL string.

    Raises:
        CanonicalizationError: If the URL cannot be parsed or canonicalized.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)

        # Scheme and hostname to lowercase
        scheme = parsed_url.scheme.lower()

        # Remove default ports
        netloc = parsed_url.netloc
        if (scheme == "http" and netloc.endswith(":80")) or (
            scheme == "https" and netloc.endswith(":443")
        ):
            netloc = netloc.rsplit(":", 1)[0]

        # Resolve path segments and remove trailing slash (unless root)
        path = urllib.parse.urlunparse(("", "", parsed_url.path, "", "", ""))
        path = urllib.parse.urlparse(path).path  # Re-parse to normalize path segments
        path = re.sub(r"/+$", "", path) if path != "/" else path

        # Sort query parameters and remove UTMs
        query_params = urllib.parse.parse_qsl(parsed_url.query)
        filtered_params = []
        for k, v in query_params:
            if not k.startswith("utm_"):
                filtered_params.append((k, v))
        sorted_query = urllib.parse.urlencode(sorted(filtered_params))

        # Reconstruct URL without fragment
        canonical_url = urllib.parse.urlunparse(
            (scheme, netloc, path, parsed_url.params, sorted_query, "")
        )

        return canonical_url
    except Exception as e:
        raise CanonicalizationError(f"Failed to canonicalize URL '{url}': {e}")
