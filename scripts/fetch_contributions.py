#!/usr/bin/env python3

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag


USERNAME = "netbyme"
OUTPUT_JSON = Path("data/contributions.json")
DEBUG_HTML = Path("data/contributions-debug.html")

CONTRIBUTION_PATTERN = re.compile(
    r"(\d[\d,]*)\s+contributions?",
    re.IGNORECASE,
)


def extract_count(cell: Tag, soup: BeautifulSoup) -> int:
    """Extract a day's exact contribution count from GitHub's markup."""

    data_count = cell.get("data-count")

    if data_count:
        try:
            return int(str(data_count).replace(",", ""))
        except ValueError:
            pass

    possible_texts: list[str] = []

    aria_label = cell.get("aria-label")
    if aria_label:
        possible_texts.append(str(aria_label))

    title = cell.get("title")
    if title:
        possible_texts.append(str(title))

    cell_text = cell.get_text(" ", strip=True)
    if cell_text:
        possible_texts.append(cell_text)

    cell_id = cell.get("id")

    if cell_id:
        tooltip = soup.find("tool-tip", attrs={"for": cell_id})

        if tooltip:
            possible_texts.append(tooltip.get_text(" ", strip=True))

    for text in possible_texts:
        if "no contributions" in text.lower():
            return 0

        match = CONTRIBUTION_PATTERN.search(text)

        if match:
            return int(match.group(1).replace(",", ""))

    return 0


def parse_contributions(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    cells = soup.select("[data-date][data-level]")

    if not cells:
        DEBUG_HTML.parent.mkdir(parents=True, exist_ok=True)
        DEBUG_HTML.write_text(html, encoding="utf-8")

        raise RuntimeError(
            "No contribution cells were found. "
            f"GitHub's response was saved to {DEBUG_HTML}."
        )

    days: list[dict[str, object]] = []

    for cell in cells:
        date = cell.get("data-date")
        raw_level = cell.get("data-level", "0")

        if not date:
            continue

        try:
            level = int(str(raw_level))
        except ValueError:
            level = 0

        level = max(0, min(level, 4))
        count = extract_count(cell, soup)

        days.append(
            {
                "date": str(date),
                "count": count,
                "level": level,
            }
        )

    unique_days = {
        str(day["date"]): day
        for day in days
    }

    sorted_days = sorted(
        unique_days.values(),
        key=lambda day: str(day["date"]),
    )

    total = sum(int(day["count"]) for day in sorted_days)

    return {
        "username": USERNAME,
        "generated_at": datetime.now(UTC).isoformat(),
        "total_contributions": total,
        "days": sorted_days,
    }


def main() -> None:
    url = f"https://github.com/users/{USERNAME}/contributions"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    data = parse_contributions(response.text)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    print(f"Saved contribution data to {OUTPUT_JSON}")
    print(f"Total contributions: {data['total_contributions']}")
    print(f"Days parsed: {len(data['days'])}")


if __name__ == "__main__":
    main()
