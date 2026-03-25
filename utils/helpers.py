"""Shared formatting and logging helpers."""

import re
from datetime import datetime


def clean_filename(name: str) -> str:
    """Remove characters that aren't safe for filenames."""
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def format_number(n: int | None) -> str:
    """Format large numbers with K/M suffixes for display."""
    if n is None:
        return "N/A"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def parse_date(date_str: str | None) -> str | None:
    """Parse various date formats into YYYY-MM-DD. Handles ISO, yt-dlp YYYYMMDD, etc."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    # yt-dlp format: YYYYMMDD
    if re.match(r"^\d{8}$", date_str):
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    # ISO format
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str


def extract_username_from_url(url: str, platform: str) -> str:
    """Extract username/handle from a platform profile URL."""
    url = url.rstrip("/")
    if platform == "instagram":
        match = re.search(r"instagram\.com/([^/?]+)", url)
    elif platform == "tiktok":
        match = re.search(r"tiktok\.com/@([^/?]+)", url)
    elif platform == "youtube":
        match = re.search(r"youtube\.com/(?:@|channel/|c/)([^/?]+)", url)
    elif platform == "linkedin":
        match = re.search(r"linkedin\.com/in/([^/?]+)", url)
    else:
        return "unknown"
    return match.group(1) if match else "unknown"
