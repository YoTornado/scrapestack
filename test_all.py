"""Non-interactive test of all scraping functions."""

import asyncio
import os
import sys

# Add ffmpeg to PATH
ffmpeg_dir = os.path.dirname(
    __import__("imageio_ffmpeg").get_ffmpeg_exe()
)
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]

from rich.console import Console

console = Console()


async def test_youtube_single():
    console.print("\n[bold magenta]═══ TEST 1: YouTube Single Video ═══[/bold magenta]")
    from platforms.youtube import scrape_single_video
    await scrape_single_video("https://www.youtube.com/watch?v=s26Erk3AK5M", model_size="base")


async def test_youtube_channel():
    console.print("\n[bold magenta]═══ TEST 2: YouTube Channel @nicksaraev last 3 ═══[/bold magenta]")
    from platforms.youtube import scrape_channel
    await scrape_channel("https://www.youtube.com/@nicksaraev", count=3, sort_by="Most Recent", model_size="base")


async def test_instagram_single():
    console.print("\n[bold magenta]═══ TEST 3: Instagram Single Reel ═══[/bold magenta]")
    from platforms.instagram import scrape_single_video
    await scrape_single_video("https://www.instagram.com/reel/DWQAD_qkQOE/", model_size="base")


async def test_instagram_account():
    console.print("\n[bold magenta]═══ TEST 4: Instagram @nick_saraev 5 most popular ═══[/bold magenta]")
    from platforms.instagram import scrape_account
    await scrape_account("https://www.instagram.com/nick_saraev/", count=5, sort_by="Most Viewed", model_size="base")


async def test_tiktok_single():
    console.print("\n[bold magenta]═══ TEST 5: TikTok Single Video ═══[/bold magenta]")
    from platforms.tiktok import scrape_single_video
    await scrape_single_video("https://www.tiktok.com/@jorge_rosb/video/7619135520618089742", model_size="base")


async def test_tiktok_account():
    console.print("\n[bold magenta]═══ TEST 6: TikTok @tornado100k 3 most recent ═══[/bold magenta]")
    from platforms.tiktok import scrape_account
    await scrape_account("https://www.tiktok.com/@tornado100k", count=3, sort_by="Most Recent", model_size="base")


async def main():
    tests = [
        ("YouTube Single Video", test_youtube_single),
        ("YouTube Channel", test_youtube_channel),
        ("Instagram Single Reel", test_instagram_single),
        ("Instagram Account", test_instagram_account),
        ("TikTok Single Video", test_tiktok_single),
        ("TikTok Account", test_tiktok_account),
    ]

    results = {}
    for name, test_fn in tests:
        try:
            await test_fn()
            results[name] = "✓ PASS"
            console.print(f"\n[bold green]✓ {name} PASSED[/bold green]")
        except Exception as e:
            results[name] = f"✗ FAIL: {e}"
            console.print(f"\n[bold red]✗ {name} FAILED: {e}[/bold red]")
            import traceback
            traceback.print_exc()

    console.print("\n[bold]═══ RESULTS SUMMARY ═══[/bold]")
    for name, result in results.items():
        color = "green" if "PASS" in result else "red"
        console.print(f"  [{color}]{result}[/{color}]  {name}")


if __name__ == "__main__":
    asyncio.run(main())
