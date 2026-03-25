"""LinkedIn scraping module — profile data extraction via Playwright."""

import asyncio
import json

from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config import LINKEDIN_DELAY, LINKEDIN_MAX_PROFILES_PER_SESSION
from core.exporter import export_to_csv
from core.rate_limiter import RateLimiter
from models.schemas import LinkedInProfile
from utils.browser import create_browser_context_with_cookies
from utils.helpers import extract_username_from_url

console = Console()
limiter = RateLimiter(delay_range=LINKEDIN_DELAY, max_concurrent=1)

COOKIES_FILE = "linkedin_cookies.json"


async def scrape_single_profile(url: str):
    """Scrape a single LinkedIn profile."""
    console.print(f"\n[bold]Scraping profile:[/bold] {url}")
    console.print("[yellow]Note:[/yellow] LinkedIn requires logged-in session cookies.")
    console.print(f"Place your cookies in [cyan]{COOKIES_FILE}[/cyan] (Netscape/JSON format).\n")

    profile = await _extract_profile(url)
    if profile:
        export_to_csv([profile], platform="linkedin", username=extract_username_from_url(url, "linkedin"))


async def scrape_batch_profiles(urls: list[str]):
    """Scrape multiple LinkedIn profiles."""
    if len(urls) > LINKEDIN_MAX_PROFILES_PER_SESSION:
        console.print(
            f"[yellow]Warning:[/yellow] Limiting to {LINKEDIN_MAX_PROFILES_PER_SESSION} "
            f"profiles per session to avoid bans."
        )
        urls = urls[:LINKEDIN_MAX_PROFILES_PER_SESSION]

    console.print(f"\n[bold]Scraping {len(urls)} LinkedIn profiles[/bold]")

    profiles: list[LinkedInProfile] = []

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), TaskProgressColumn(),
    ) as progress:
        task = progress.add_task("Scraping profiles...", total=len(urls))

        for i, url in enumerate(urls):
            progress.update(task, description=f"Profile {i+1}/{len(urls)}...")
            try:
                profile = await _extract_profile(url)
                if profile:
                    profiles.append(profile)
            except Exception as e:
                console.print(f"  [red]Failed {url}:[/red] {e}")

            progress.advance(task)
            await limiter.wait()

    export_to_csv(profiles, platform="linkedin", username="batch")


async def scrape_search(query: str, max_results: int):
    """Scrape LinkedIn profiles from a search query."""
    console.print(f"\n[bold]Searching LinkedIn:[/bold] \"{query}\" (max {max_results} profiles)")
    console.print("[yellow]Note:[/yellow] Search scraping requires logged-in session cookies.\n")

    profile_urls = await _search_profiles(query, max_results)
    if not profile_urls:
        console.print("[red]No profiles found.[/red]")
        return

    console.print(f"Found {len(profile_urls)} profiles. Scraping details...")
    await scrape_batch_profiles(profile_urls)


async def _extract_profile(url: str) -> LinkedInProfile | None:
    """Extract profile data from a LinkedIn profile page."""
    async with async_playwright() as p:
        browser, context = await create_browser_context_with_cookies(p, COOKIES_FILE)
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # Extract basic info
            name_el = await page.query_selector("h1")
            name = await name_el.inner_text() if name_el else None

            headline_el = await page.query_selector(".text-body-medium")
            headline = await headline_el.inner_text() if headline_el else None

            location_el = await page.query_selector(".text-body-small.inline.t-black--light")
            location = await location_el.inner_text() if location_el else None

            # About section
            bio = None
            about_section = await page.query_selector("#about ~ div .inline-show-more-text")
            if about_section:
                bio = await about_section.inner_text()

            # Experience
            experience = await _extract_experience(page)

            # Education
            school, major, grad_year = await _extract_education(page)

            # Skills
            skills = await _extract_skills(page)

            return LinkedInProfile(
                name=name,
                headline=headline,
                location=location,
                bio=bio,
                current_school=school,
                major=major,
                graduation_year=grad_year,
                experience=experience,
                skills=skills,
                profile_url=url,
            )
        except Exception as e:
            console.print(f"  [red]Error extracting profile:[/red] {e}")
            return None
        finally:
            await browser.close()


async def _extract_experience(page) -> list[dict]:
    """Extract experience entries from the profile page."""
    experience = []
    try:
        exp_items = await page.query_selector_all("#experience ~ div ul > li")
        for item in exp_items[:10]:  # Limit to avoid excessive scraping
            title_el = await item.query_selector(".t-bold span")
            company_el = await item.query_selector(".t-normal span")
            title = await title_el.inner_text() if title_el else None
            company = await company_el.inner_text() if company_el else None
            if title or company:
                experience.append({"title": title, "company": company})
    except Exception:
        pass
    return experience


async def _extract_education(page) -> tuple[str | None, str | None, str | None]:
    """Extract the most recent education entry."""
    try:
        edu_item = await page.query_selector("#education ~ div ul > li")
        if edu_item:
            school_el = await edu_item.query_selector(".t-bold span")
            school = await school_el.inner_text() if school_el else None

            details = await edu_item.query_selector_all(".t-normal span")
            major = await details[0].inner_text() if len(details) > 0 else None
            grad_year = await details[1].inner_text() if len(details) > 1 else None
            return school, major, grad_year
    except Exception:
        pass
    return None, None, None


async def _extract_skills(page) -> list[str]:
    """Extract listed skills."""
    skills = []
    try:
        skill_items = await page.query_selector_all("#skills ~ div ul > li .t-bold span")
        for item in skill_items[:20]:
            text = await item.inner_text()
            if text:
                skills.append(text.strip())
    except Exception:
        pass
    return skills


async def _search_profiles(query: str, max_results: int) -> list[str]:
    """Search LinkedIn and collect profile URLs from results."""
    urls = []
    async with async_playwright() as p:
        browser, context = await create_browser_context_with_cookies(p, COOKIES_FILE)
        page = await context.new_page()

        try:
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={query}"
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            page_num = 1
            while len(urls) < max_results:
                links = await page.query_selector_all('a[href*="/in/"]')
                for link in links:
                    href = await link.get_attribute("href")
                    if href and "/in/" in href and href not in urls:
                        # Clean the URL
                        clean = href.split("?")[0]
                        if clean not in urls:
                            urls.append(clean)

                if len(urls) >= max_results:
                    break

                # Try next page
                page_num += 1
                next_btn = await page.query_selector(f'button[aria-label="Page {page_num}"]')
                if not next_btn:
                    break
                await next_btn.click()
                await page.wait_for_timeout(3000)
        finally:
            await browser.close()

    return urls[:max_results]
