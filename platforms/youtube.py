"""YouTube scraping module — channel/video/playlist with transcription."""

import tempfile
from pathlib import Path

import yt_dlp
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config import YOUTUBE_DELAY
from core.downloader import extract_audio, get_video_info
from core.exporter import export_to_csv
from core.rate_limiter import RateLimiter
from core.transcriber import get_transcript
from models.schemas import YouTubeVideo
from utils.helpers import extract_username_from_url, parse_date

console = Console()
limiter = RateLimiter(delay_range=YOUTUBE_DELAY)


async def scrape_single_video(url: str, model_size: str = "base"):
    """Scrape and transcribe a single YouTube video."""
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

        transcript = await get_transcript(url, audio_path, model_size, platform="youtube")

    video = YouTubeVideo(
        video_url=url,
        title=info.get("title"),
        publish_date=parse_date(info.get("upload_date")),
        description=info.get("description"),
        views=info.get("view_count"),
        likes=info.get("like_count"),
        comments_count=info.get("comment_count"),
        duration=str(info.get("duration", "")),
        transcript=transcript,
        tags=info.get("tags"),
    )

    export_to_csv([video], platform="youtube", username="single_video")


async def scrape_channel(url: str, count: int, sort_by: str, model_size: str = "base"):
    """Scrape a YouTube channel's videos with transcription."""
    username = extract_username_from_url(url, "youtube")
    console.print(f"\n[bold]Scraping channel:[/bold] {username} ({count} videos, {sort_by})")

    video_urls = _get_channel_video_urls(url, count, sort_by)
    if not video_urls:
        console.print("[red]No videos found.[/red]")
        return

    videos = await _process_video_list(video_urls, model_size)
    export_to_csv(videos, platform="youtube", username=username)


async def scrape_playlist(url: str, model_size: str = "base"):
    """Scrape all videos in a YouTube playlist."""
    console.print(f"\n[bold]Scraping playlist:[/bold] {url}")

    video_urls = _get_playlist_video_urls(url)
    if not video_urls:
        console.print("[red]No videos found in playlist.[/red]")
        return

    videos = await _process_video_list(video_urls, model_size)
    export_to_csv(videos, platform="youtube", username="playlist")


async def _process_video_list(video_urls: list[str], model_size: str) -> list[YouTubeVideo]:
    """Download, transcribe, and collect data for a list of video URLs."""
    videos: list[YouTubeVideo] = []

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
                transcript = await get_transcript(vurl, audio_path, model_size, platform="youtube")

                video = YouTubeVideo(
                    video_url=vurl,
                    title=info.get("title"),
                    publish_date=parse_date(info.get("upload_date")),
                    description=info.get("description"),
                    views=info.get("view_count"),
                    likes=info.get("like_count"),
                    comments_count=info.get("comment_count"),
                    duration=str(info.get("duration", "")),
                    transcript=transcript,
                    tags=info.get("tags"),
                )
                videos.append(video)
            except Exception as e:
                console.print(f"  [red]Failed video {i+1}:[/red] {e}")

            progress.advance(task)
            await limiter.wait()

    return videos


def _get_channel_video_urls(channel_url: str, count: int, sort_by: str) -> list[str]:
    """Extract video URLs from a YouTube channel using yt-dlp."""
    # Ensure we're looking at the videos tab
    if "/videos" not in channel_url:
        channel_url = channel_url.rstrip("/") + "/videos"

    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlist_end": count * 2 if sort_by == "Most Viewed" else count,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        entries = info.get("entries", [])

    urls_with_views = []
    for entry in entries:
        if entry and entry.get("url"):
            video_url = f"https://www.youtube.com/watch?v={entry['url']}" if len(entry['url']) == 11 else entry['url']
            urls_with_views.append((video_url, entry.get("view_count", 0) or 0))

    if sort_by == "Most Viewed":
        urls_with_views.sort(key=lambda x: x[1], reverse=True)

    return [url for url, _ in urls_with_views[:count]]


def _get_playlist_video_urls(playlist_url: str) -> list[str]:
    """Extract all video URLs from a YouTube playlist."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        entries = info.get("entries", [])

    urls = []
    for entry in entries:
        if entry and entry.get("url"):
            video_url = f"https://www.youtube.com/watch?v={entry['url']}" if len(entry['url']) == 11 else entry['url']
            urls.append(video_url)

    return urls
