"""Instagram scraping module — profile data + Reels with transcription."""

import asyncio
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config import INSTAGRAM_DELAY
from core.downloader import extract_audio, get_video_info
from core.exporter import export_to_csv
from core.rate_limiter import RateLimiter
from core.transcriber import get_transcript
from models.schemas import InstagramVideo, InstagramAccount
from utils.browser import create_browser_context
from utils.helpers import extract_username_from_url, parse_date

console = Console()
limiter = RateLimiter(delay_range=INSTAGRAM_DELAY)


async def scrape_single_video(url: str, model_size: str = "base"):
    """Scrape a single Instagram Reel/video and transcribe it."""
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

        transcript = await get_transcript(url, audio_path, model_size, platform="instagram")

    video = InstagramVideo(
        video_url=url,
        post_date=parse_date(info.get("upload_date")),
        caption=info.get("description", ""),
        likes=info.get("like_count"),
        comments=info.get("comment_count"),
        views=info.get("view_count"),
        duration_seconds=info.get("duration"),
        transcript=transcript,
    )

    export_to_csv([video], platform="instagram", username="single_video")


async def scrape_account(url: str, count: int, sort_by: str, model_size: str = "base"):
    """Scrape an Instagram account's Reels with transcription."""
    username = extract_username_from_url(url, "instagram")
    console.print(f"\n[bold]Scraping account:[/bold] @{username} ({count} videos, {sort_by})")

    # Step 1: Collect reel URLs from profile page
    # Fetch more than needed if sorting by views (we need metadata to sort)
    fetch_count = count * 3 if sort_by == "Most Viewed" else count
    video_urls = await _get_profile_video_urls(url, username, fetch_count)
    if not video_urls:
        console.print("[red]No videos found.[/red]")
        return

    console.print(f"Found {len(video_urls)} reel URLs")

    # Step 2: If sorting by Most Viewed, get metadata for all and sort
    if sort_by == "Most Viewed":
        console.print("Fetching metadata to sort by views...")
        url_views = []
        for vurl in video_urls:
            try:
                info = get_video_info(vurl)
                views = info.get("view_count") or info.get("like_count") or 0
                url_views.append((vurl, views))
            except Exception:
                url_views.append((vurl, 0))
            await limiter.wait()
        url_views.sort(key=lambda x: x[1], reverse=True)
        video_urls = [u for u, _ in url_views[:count]]
        console.print(f"Top {count} by views selected")
    else:
        video_urls = video_urls[:count]

    # Step 3: Download, transcribe, collect data
    videos: list[InstagramVideo] = []

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), TaskProgressColumn(),
    ) as progress:
        task = progress.add_task("Processing videos...", total=len(video_urls))

        for i, vurl in enumerate(video_urls):
            try:
                progress.update(task, description=f"Downloading video {i+1}/{len(video_urls)}...")
                info = get_video_info(vurl)

                tmp_dir = Path(tempfile.mkdtemp())
                audio_path = extract_audio(vurl, tmp_dir)

                progress.update(task, description=f"Transcribing video {i+1}/{len(video_urls)}...")
                transcript = await get_transcript(vurl, audio_path, model_size, platform="instagram")

                video = InstagramVideo(
                    video_url=vurl,
                    post_date=parse_date(info.get("upload_date")),
                    caption=info.get("description", ""),
                    likes=info.get("like_count"),
                    comments=info.get("comment_count"),
                    views=info.get("view_count"),
                    duration_seconds=info.get("duration"),
                    transcript=transcript,
                )
                videos.append(video)
            except Exception as e:
                console.print(f"  [red]Failed video {i+1}:[/red] {e}")

            progress.advance(task)
            if i < len(video_urls) - 1:
                await limiter.wait()

    # Step 4: Export
    account_summary = {"username": username, "videos_scraped": len(videos)}
    export_to_csv(videos, platform="instagram", username=username, account_summary=account_summary)


async def _get_profile_video_urls(profile_url: str, username: str, max_count: int) -> list[str]:
    """Use Playwright to scroll the profile and collect Reel URLs."""
    urls = []
    reels_url = profile_url.rstrip("/") + "/reels/"

    async with async_playwright() as p:
        browser, context = await create_browser_context(p)
        page = await context.new_page()

        try:
            await page.goto(reels_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            last_count = 0
            scroll_attempts = 0
            while len(urls) < max_count and scroll_attempts < 30:
                links = await page.query_selector_all('a[href*="/reel/"]')
                for link in links:
                    href = await link.get_attribute("href")
                    if href:
                        full_url = f"https://www.instagram.com{href}" if href.startswith("/") else href
                        if full_url not in urls:
                            urls.append(full_url)

                if len(urls) >= max_count:
                    break

                if len(urls) == last_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                last_count = len(urls)

                await page.evaluate("window.scrollBy(0, 1500)")
                await page.wait_for_timeout(2000)
        finally:
            await browser.close()

    return urls[:max_count]
