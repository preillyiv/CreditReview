"""Company logo fetching via Clearbit."""

import requests
from pathlib import Path
from urllib.parse import urlparse


def get_logo_url(domain: str) -> str:
    """
    Get Clearbit logo URL for a domain.

    Args:
        domain: Company domain (e.g., 'verizon.com')

    Returns:
        URL to company logo image
    """
    # Clean domain if full URL was passed
    if domain.startswith(("http://", "https://")):
        domain = urlparse(domain).netloc

    return f"https://logo.clearbit.com/{domain}"


def download_logo(domain: str, output_path: Path) -> Path | None:
    """
    Download company logo to a file.

    Args:
        domain: Company domain (e.g., 'verizon.com')
        output_path: Directory to save the logo

    Returns:
        Path to downloaded logo, or None if not found
    """
    url = get_logo_url(domain)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Determine file extension from content type
        content_type = response.headers.get("content-type", "image/png")
        ext = "png" if "png" in content_type else "jpg"

        logo_file = output_path / f"logo.{ext}"
        logo_file.write_bytes(response.content)

        return logo_file

    except requests.RequestException:
        return None


def get_domain_from_website(website_url: str) -> str:
    """
    Extract domain from a website URL.

    Args:
        website_url: Full website URL

    Returns:
        Domain name
    """
    if not website_url:
        return ""

    parsed = urlparse(website_url)
    domain = parsed.netloc or parsed.path

    # Remove www. prefix if present
    if domain.startswith("www."):
        domain = domain[4:]

    return domain
