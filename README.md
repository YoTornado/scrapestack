# ScrapeStack

Multi-platform web scraping & video transcription CLI tool. Scrapes public data from **Instagram**, **TikTok**, **YouTube**, and **LinkedIn**, with bulk video transcription and engagement metrics exported as structured CSV data.

## What It Does

- Downloads videos from Instagram Reels, TikTok, and YouTube
- Transcribes them using OpenAI Whisper (runs locally, no API key needed)
- For YouTube, pulls existing captions first (faster) and falls back to Whisper
- Collects engagement metrics (likes, comments, views, shares)
- Scrapes LinkedIn profiles for education, experience, and skills
- Exports everything to clean CSV files

## Requirements

- **Python 3.11+**
- **ffmpeg** — either install system-wide or the tool auto-detects `imageio-ffmpeg` as a fallback

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install imageio-ffmpeg if you don't have ffmpeg on your PATH
pip install imageio-ffmpeg

# Install Playwright browser
playwright install chromium
```

### Environment Variables (Optional)

```bash
YOUTUBE_API_KEY=...   # YouTube Data API v3 key
OPENAI_API_KEY=...    # For future AI summary features
```

## Usage

```bash
python main.py
```

The interactive menu walks you through platform selection, scrape mode, URLs, video count, sorting, and transcript quality.

```
┌───────────────────────────────────────────────────┐
│ ScrapeStack v1.0                                  │
│ Multi-Platform Web Scraping & Video Transcription │
└───────────────────────────────────────────────────┘
? Select a platform:
  > Instagram
    TikTok
    YouTube
    LinkedIn
    Exit
```

## Platforms

### YouTube

| Mode | Description |
|------|-------------|
| Single Video | Scrape and transcribe one video |
| Channel Scrape | Last N videos from a channel, sorted by recent or views |
| Playlist | All videos in a playlist |

**Data collected per video:** `video_url`, `title`, `publish_date`, `description`, `views`, `likes`, `comments_count`, `duration`, `transcript`, `tags`

**Transcription strategy:** Pulls existing YouTube captions via `youtube-transcript-api` first (instant, free). Falls back to Whisper if no captions exist.

### Instagram

| Mode | Description |
|------|-------------|
| Single Video Transcript | Scrape and transcribe one Reel |
| Full Account Scrape | Last N Reels from a profile, sorted by recent or most liked |

**Data collected per video:** `video_url`, `post_date`, `caption`, `likes`, `comments`, `views`, `duration_seconds`, `transcript`

> Note: Instagram doesn't expose view counts for Reels via yt-dlp, so "Most Viewed" sorting uses like count as a proxy.

### TikTok

| Mode | Description |
|------|-------------|
| Single Video Transcript | Scrape and transcribe one video |
| Full Account Scrape | Last N videos from a profile, sorted by recent or views |

**Data collected per video:** `video_url`, `post_date`, `caption`, `likes`, `comments`, `shares`, `views`, `duration_seconds`, `transcript`, `sounds`

### LinkedIn

| Mode | Description |
|------|-------------|
| Single Profile | Scrape one profile |
| Batch Profiles | Scrape a list of profiles (paste URLs or load from file) |
| Search Scrape | Search LinkedIn and scrape resulting profiles |

**Data collected per profile:** `name`, `headline`, `location`, `bio`, `current_school`, `major`, `graduation_year`, `experience`, `skills`, `profile_url`

> LinkedIn requires a logged-in session. Export your cookies to `linkedin_cookies.json` in the project root. **Never commit this file** — it's in `.gitignore`.

## Transcription Quality

You pick the Whisper model at runtime:

| Option | Model | Speed | Quality |
|--------|-------|-------|---------|
| Fast | `base` | ~10x realtime | Good for bulk jobs |
| Balanced | `medium` | ~3x realtime | Good accuracy |
| Best | `large-v3` | ~1x realtime | Highest accuracy |

All transcription runs locally on CPU (no GPU required). First run downloads the model (~150MB for base, ~4GB for large-v3).

## Output

CSV files are saved to the `output/` directory:

```
output/
  garyvee_instagram_2026-03-24.csv
  garyvee_instagram_2026-03-24_summary.csv
  nicksaraev_youtube_2026-03-24.csv
```

Each CSV has one row per video/profile. Account scrapes also generate a `_summary.csv` with account-level metadata.

## Project Structure

```
scrapestack/
├── main.py                    # CLI entry point, interactive menu
├── config.py                  # Settings, API keys, rate limits
├── requirements.txt
├── core/
│   ├── transcriber.py         # Whisper pipeline + YouTube caption fallback
│   ├── downloader.py          # yt-dlp wrapper (download, extract audio, metadata)
│   ├── exporter.py            # CSV generation
│   └── rate_limiter.py        # Async rate limiter with random delays
├── platforms/
│   ├── instagram.py           # IG scraping (Playwright + yt-dlp)
│   ├── tiktok.py              # TikTok scraping (yt-dlp)
│   ├── youtube.py             # YouTube scraping (yt-dlp)
│   └── linkedin.py            # LinkedIn scraping (Playwright + cookies)
├── models/
│   └── schemas.py             # Pydantic data models
├── utils/
│   ├── browser.py             # Playwright session + user agent rotation
│   └── helpers.py             # Date parsing, URL extraction, formatting
└── output/                    # Generated CSVs (gitignored)
```

## Rate Limiting & Anti-Detection

| Platform | Strategy |
|----------|----------|
| Instagram | 2-4 sec random delays, user agent rotation |
| TikTok | 2-4 sec delays, yt-dlp handles extraction |
| YouTube | 1-2 sec delays, captions API avoids downloads when possible |
| LinkedIn | 5-10 sec delays, max 100 profiles/session, requires session cookies |

## Troubleshooting

**`ffmpeg not found`** — Install ffmpeg system-wide, or run `pip install imageio-ffmpeg` (auto-detected as fallback).

**`cublas64_12.dll not found`** — Whisper tried to use GPU. The tool is configured for CPU-only (`device="cpu"`) so this shouldn't happen. If it does, check your `faster-whisper` installation.

**Instagram returns no videos** — Instagram may require login for some profiles. The tool works without login for public profiles with public Reels.

**LinkedIn scraping fails** — You need a valid `linkedin_cookies.json` with your session cookies. Export them from your browser using a cookie export extension.

## Disclaimer

This tool is intended for personal research, competitor analysis, and educational use. Respect each platform's Terms of Service. Scraped data may contain personal information — handle it responsibly and do not redistribute without consent.
