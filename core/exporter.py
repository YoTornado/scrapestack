"""CSV / Excel export for scraped data."""

from datetime import datetime
from pathlib import Path

import pandas as pd
from pydantic import BaseModel
from rich.console import Console

from config import OUTPUT_DIR

console = Console()


def export_to_csv(
    data: list[BaseModel],
    platform: str,
    username: str = "export",
    account_summary: dict | None = None,
) -> Path:
    """Export a list of Pydantic models to CSV. Returns the output file path."""
    rows = [item.model_dump() for item in data]
    df = pd.DataFrame(rows)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"{username}_{platform}_{timestamp}.csv"
    filepath = OUTPUT_DIR / filename

    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    console.print(f"\n[bold green]✓[/bold green] Data saved to: [cyan]{filepath}[/cyan]")

    # Write account summary to a separate file if provided
    if account_summary:
        summary_filename = f"{username}_{platform}_{timestamp}_summary.csv"
        summary_path = OUTPUT_DIR / summary_filename
        summary_df = pd.DataFrame([account_summary])
        summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
        console.print(f"[bold green]✓[/bold green] Summary saved to: [cyan]{summary_path}[/cyan]")

    return filepath
