"""Playwright browser session management."""

import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


async def create_browser_context(playwright, headless: bool = True):
    """Create a Playwright browser context with randomized user agent."""
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
    )
    return browser, context


async def create_browser_context_with_cookies(
    playwright, cookies_file: str | None = None, headless: bool = True
):
    """Create a browser context and optionally load cookies from a file."""
    import json
    from pathlib import Path

    browser, context = await create_browser_context(playwright, headless)

    if cookies_file and Path(cookies_file).exists():
        with open(cookies_file) as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

    return browser, context
