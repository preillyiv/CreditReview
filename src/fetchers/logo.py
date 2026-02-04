"""Company logo fetching with multiple provider fallbacks."""

import io
import os
import requests
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image


def _get_logo_dev_token() -> str:
    """Get Logo.dev token from environment or use default."""
    return os.environ.get("LOGO_DEV_TOKEN", "")


def get_logo_url(domain: str, provider: str = "logo_dev") -> str:
    """
    Get logo URL for a domain from various providers.

    Args:
        domain: Company domain (e.g., 'verizon.com')
        provider: Logo provider ('logo_dev', 'clearbit', 'google', 'duckduckgo')

    Returns:
        URL to company logo image
    """
    # Clean domain if full URL was passed
    if domain.startswith(("http://", "https://")):
        domain = urlparse(domain).netloc
    if domain.startswith("www."):
        domain = domain[4:]

    if provider == "logo_dev":
        token = _get_logo_dev_token()
        return f"https://img.logo.dev/{domain}?token={token}"
    elif provider == "clearbit":
        return f"https://logo.clearbit.com/{domain}"
    elif provider == "google":
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    elif provider == "duckduckgo":
        return f"https://icons.duckduckgo.com/ip3/{domain}.ico"
    else:
        token = _get_logo_dev_token()
        return f"https://img.logo.dev/{domain}?token={token}"


def download_logo(domain: str, output_path: Path) -> Path | None:
    """
    Download company logo to a file, trying multiple providers.

    Images are converted to PNG for best compatibility with python-docx.

    Args:
        domain: Company domain (e.g., 'verizon.com')
        output_path: Directory to save the logo

    Returns:
        Path to downloaded logo, or None if not found
    """
    # Ensure output_path is a directory
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Try providers in order of quality
    providers = ["logo_dev", "clearbit", "google", "duckduckgo"]

    for provider in providers:
        url = get_logo_url(domain, provider)

        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()

            # Check we got actual image content (not an error page)
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                continue

            # Skip tiny images (likely error placeholders)
            if len(response.content) < 100:
                continue

            # Convert to PNG for best python-docx compatibility
            try:
                img = Image.open(io.BytesIO(response.content))
                # Convert to RGB if necessary (handles RGBA, P mode, etc.)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                logo_file = output_path / "logo.png"
                img.save(logo_file, "PNG")
                return logo_file
            except Exception:
                # If conversion fails, save raw bytes as fallback
                logo_file = output_path / "logo.png"
                logo_file.write_bytes(response.content)
                return logo_file

        except requests.RequestException:
            continue  # Try next provider

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
