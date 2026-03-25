"""ScrapeStack v1.0 — Multi-Platform Web Scraping & Video Transcription Tool."""

import asyncio
from rich.console import Console
from rich.panel import Panel
import questionary

from config import WHISPER_MODEL_MAP

console = Console()


def show_banner():
    console.print(
        Panel(
            "[bold cyan]ScrapeStack v1.0[/bold cyan]\n"
            "Multi-Platform Web Scraping & Video Transcription",
            expand=False,
            border_style="bright_blue",
        )
    )


# ── Platform menu handlers ─────────────────────────────────


async def handle_instagram():
    from platforms.instagram import scrape_account, scrape_single_video

    mode = questionary.select(
        "Select mode:",
        choices=["Full Account Scrape", "Single Video Transcript"],
    ).ask()
    if mode is None:
        return

    if mode == "Single Video Transcript":
        url = questionary.text("Paste the video URL:").ask()
        if not url:
            return
        quality = _ask_transcript_quality()
        if quality is None:
            return
        await scrape_single_video(url, quality)
    else:
        url = questionary.text("Paste the profile URL:").ask()
        if not url:
            return
        count = questionary.text("How many videos?", default="10").ask()
        sort_by = questionary.select(
            "Sort by:", choices=["Most Recent", "Most Viewed"]
        ).ask()
        quality = _ask_transcript_quality()
        if any(v is None for v in [count, sort_by, quality]):
            return
        await scrape_account(url, int(count), sort_by, quality)


async def handle_tiktok():
    from platforms.tiktok import scrape_account, scrape_single_video

    mode = questionary.select(
        "Select mode:",
        choices=["Full Account Scrape", "Single Video Transcript"],
    ).ask()
    if mode is None:
        return

    if mode == "Single Video Transcript":
        url = questionary.text("Paste the video URL:").ask()
        if not url:
            return
        quality = _ask_transcript_quality()
        if quality is None:
            return
        await scrape_single_video(url, quality)
    else:
        url = questionary.text("Paste the profile URL:").ask()
        if not url:
            return
        count = questionary.text("How many videos?", default="10").ask()
        sort_by = questionary.select(
            "Sort by:", choices=["Most Recent", "Most Viewed"]
        ).ask()
        quality = _ask_transcript_quality()
        if any(v is None for v in [count, sort_by, quality]):
            return
        await scrape_account(url, int(count), sort_by, quality)


async def handle_youtube():
    from platforms.youtube import scrape_channel, scrape_single_video, scrape_playlist

    mode = questionary.select(
        "Select mode:",
        choices=["Channel Scrape", "Single Video", "Playlist"],
    ).ask()
    if mode is None:
        return

    if mode == "Single Video":
        url = questionary.text("Paste the video URL:").ask()
        if not url:
            return
        quality = _ask_transcript_quality()
        if quality is None:
            return
        await scrape_single_video(url, quality)
    elif mode == "Playlist":
        url = questionary.text("Paste the playlist URL:").ask()
        if not url:
            return
        quality = _ask_transcript_quality()
        if quality is None:
            return
        await scrape_playlist(url, quality)
    else:
        url = questionary.text("Paste the channel URL:").ask()
        if not url:
            return
        count = questionary.text("How many videos?", default="10").ask()
        sort_by = questionary.select(
            "Sort by:", choices=["Most Recent", "Most Viewed"]
        ).ask()
        quality = _ask_transcript_quality()
        if any(v is None for v in [count, sort_by, quality]):
            return
        await scrape_channel(url, int(count), sort_by, quality)


async def handle_linkedin():
    from platforms.linkedin import scrape_single_profile, scrape_batch_profiles, scrape_search

    mode = questionary.select(
        "Select mode:",
        choices=["Single Profile", "Batch Profiles", "Search Scrape"],
    ).ask()
    if mode is None:
        return

    if mode == "Single Profile":
        url = questionary.text("Paste the profile URL:").ask()
        if not url:
            return
        await scrape_single_profile(url)
    elif mode == "Batch Profiles":
        source = questionary.select(
            "Input method:", choices=["Paste URLs", "From file"]
        ).ask()
        if source == "Paste URLs":
            raw = questionary.text("Paste URLs (comma-separated):").ask()
            if not raw:
                return
            urls = [u.strip() for u in raw.split(",") if u.strip()]
        else:
            path = questionary.text("Path to file with URLs (one per line):").ask()
            if not path:
                return
            with open(path) as f:
                urls = [line.strip() for line in f if line.strip()]
        await scrape_batch_profiles(urls)
    else:
        query = questionary.text("Enter search query:").ask()
        max_results = questionary.text("Max profiles to scrape:", default="25").ask()
        if not query or max_results is None:
            return
        await scrape_search(query, int(max_results))


# ── Helpers ─────────────────────────────────────────────────


def _ask_transcript_quality() -> str | None:
    choice = questionary.select(
        "Transcript quality:",
        choices=list(WHISPER_MODEL_MAP.keys()),
    ).ask()
    if choice is None:
        return None
    return WHISPER_MODEL_MAP[choice]


PLATFORM_HANDLERS = {
    "Instagram": handle_instagram,
    "TikTok": handle_tiktok,
    "YouTube": handle_youtube,
    "LinkedIn": handle_linkedin,
}


# ── Main loop ───────────────────────────────────────────────


async def main():
    show_banner()

    while True:
        platform = questionary.select(
            "Select a platform:",
            choices=list(PLATFORM_HANDLERS.keys()) + ["Exit"],
        ).ask()

        if platform is None or platform == "Exit":
            console.print("[bold]Goodbye![/bold]")
            break

        try:
            await PLATFORM_HANDLERS[platform]()
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
