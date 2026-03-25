"""ScrapeStack configuration — API keys, paths, defaults."""

import os
import sys

# Fix Windows console encoding for Rich
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Whisper settings
WHISPER_MODEL_MAP = {
    "Fast (base model)": "base",
    "Balanced (medium model)": "medium",
    "Best (large-v3)": "large-v3",
}
DEFAULT_WHISPER_MODEL = "base"

# Rate limiting defaults (seconds)
INSTAGRAM_DELAY = (2, 4)
TIKTOK_DELAY = (2, 4)
YOUTUBE_DELAY = (1, 2)
LINKEDIN_DELAY = (5, 10)

# LinkedIn session limits
LINKEDIN_MAX_PROFILES_PER_SESSION = 100

# Optional API keys (set via environment variables)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
