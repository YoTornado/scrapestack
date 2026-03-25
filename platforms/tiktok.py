"""TikTok scraping module — profile data + videos with transcription."""

import asyncio
import tempfile
from pathlib import Path

import yt_dlp
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config import TIKTOK_DELAY
from core.downloader import extract_audio, get_video_info, _base_opts
from core.exporter import export_to_csv
from core.rate_limiter import RateLimiter
from core.transcriber import get_transcript
from models.schemas import TikTokVideo, TikTokAccount
from utils.helpers import extract_username_from_url, parse_date

console = Console()
limiter = RateLimiter(delay_range=TIKTOK_DELAY)


async def scrape_single_video(url: str, model_size: str = "base"):
    """Scrape and transcribe a single TikTok video."""
    console.print(f"\n[bold]Scraping single video:[/bold] {url}")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("Getting video info...", total=None)

        info = get_video_info(url)
        progress.update(task, description="Downloading audio...")

        tmp_dir = Path(tempfile.mkdtemp())
        audio_path = extract_audio(url, tmp_dir)
        progress.update(task, description="Transcribing...")

        transcript = await get_transcript(url, audio_path, model_size, platform="tiktok")

    video = TikTokVideo(
        video_url=url,
        post_date=parse_date(info.get("upload_date")),
        caption=info.get("description", ""),
        likes=info.get("like_count"),
        comments=info.get("comment_count"),
        shares=info.get("repost_count"),
        views=info.get("view_count"),
        duration_seconds=info.get("duration"),
        transcript=transcript,
        sounds=info.get("track"),
    )

    export_to_csv([video], platform="tiktok", username="single_video")


async def scrape_account(url: str, count: int, sort_by: str, model_size: str = "base"):
    """Scrape a TikTok account's videos with transcription."""
    username = extract_username_from_url(url, "tiktok")
    console.print(f"\n[bold]Scraping account:[/bold] @{username} ({count} videos, {sort_by})")

    # Use yt-dlp to extract video URLs from TikTok profile
    video_entries = _get_profile_videos(url, count, sort_by)
    if not video_entries:
        console.print("[red]No videos found.[/red]")
        return

    video_urls = [e["url"] for e in video_entries]
    console.print(f"Found {len(video_urls)} videos")

    # Download, transcribe, collect data
    videos: list[TikTokVideo] = []

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), TaskProgressColumn(),
    ) as progress:
        task = progress.add_task("Processing videos...", total=len(video_urls))

        for i, vurl in enumerate(video_urls):
            try:
                progress.update(task, description=f"Downloading {i+1}/{len(video_urls)}...")
                info = get_video_info(vurl)

                tmp_dir = Path(tempfile.mkdtemp())
                audio_path = extract_audio(vurl, tmp_dir)

                progress.update(task, description=f"Transcribing {i+1}/{len(video_urls)}...")
                transcript = await get_transcript(vurl, audio_path, model_size, platform="tiktok")

                video = TikTokVideo(
                    video_url=vurl,
                    post_date=parse_date(info.get("upload_date")),
                    caption=info.get("description", ""),
                    likes=info.get("like_count"),
                    comments=info.get("comment_count"),
                    shares=info.get("repost_count"),
                    views=info.get("view_count"),
                    duration_seconds=info.get("duration"),
                    transcript=transcript,
                    sounds=info.get("track"),
                )
                videos.append(video)
            except Exception as e:
                console.print(f"  [red]Failed video {i+1}:[/red] {e}")

            progress.advance(task)
            if i < len(video_urls) - 1:
                await limiter.wait()

    account_summary = {"username": username, "videos_scraped": len(videos)}
    export_to_csv(videos, platform="tiktok", username=username, account_summary=account_summary)


def _get_profile_videos(profile_url: str, count: int, sort_by: str) -> list[dict]:
    """Extract video entries from a TikTok profile using yt-dlp."""
    opts = _base_opts()
    opts.update({
        "extract_flat": True,
        # Fetch extra if sorting by views
        "playlist_end": count * 3 if sort_by == "Most Viewed" else count,
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(profile_url, download=False)
        entries = [e for e in (info.get("entries") or []) if e and e.get("url")]

    if sort_by == "Most Viewed":
        entries.sort(key=lambda x: x.get("view_count", 0) or 0, reverse=True)

    return entries[:count]
