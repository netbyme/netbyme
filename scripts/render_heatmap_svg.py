#!/usr/bin/env python3

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape


INPUT_PATH = Path("data/contributions.json")
OUTPUT_PATH = Path("assets/contribution-heatmap.svg")

WIDTH = 860
HEIGHT = 225

BACKGROUND = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
BLUE = "#58a6ff"

PALETTE = {
    0: "#21262d",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}

CELL_SIZE = 11
CELL_GAP = 3
CELL_STEP = CELL_SIZE + CELL_GAP

GRID_LEFT = 52
GRID_TOP = 54

FONT_FAMILY = (
    "JetBrains Mono, Cascadia Code, SFMono-Regular, "
    "Consolas, Liberation Mono, monospace"
)


def load_data() -> dict:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Contribution data not found: {INPUT_PATH}"
        )

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if "days" not in data or not isinstance(data["days"], list):
        raise ValueError("Invalid contribution data.")

    return data


def parse_days(data: dict) -> dict[date, dict]:
    parsed: dict[date, dict] = {}

    for item in data["days"]:
        contribution_date = datetime.strptime(
            item["date"],
            "%Y-%m-%d",
        ).date()

        parsed[contribution_date] = {
            "count": int(item.get("count", 0)),
            "level": max(0, min(int(item.get("level", 0)), 4)),
        }

    return parsed


def calculate_streaks(
    days: dict[date, dict],
) -> tuple[int, int]:
    if not days:
        return 0, 0

    ordered_dates = sorted(days)
    longest_streak = 0
    running_streak = 0

    for current_date in ordered_dates:
        if days[current_date]["count"] > 0:
            running_streak += 1
            longest_streak = max(longest_streak, running_streak)
        else:
            running_streak = 0

    latest_date = ordered_dates[-1]

    if days[latest_date]["count"] == 0:
        latest_date -= timedelta(days=1)

    current_streak = 0
    cursor = latest_date

    while cursor in days and days[cursor]["count"] > 0:
        current_streak += 1
        cursor -= timedelta(days=1)

    return current_streak, longest_streak


def find_best_day(
    days: dict[date, dict],
) -> tuple[date | None, int]:
    if not days:
        return None, 0

    best_date = max(
        days,
        key=lambda contribution_date: days[contribution_date]["count"],
    )

    return best_date, days[best_date]["count"]


def get_grid_dates(
    days: dict[date, dict],
) -> tuple[date, date]:
    first_date = min(days)
    last_date = max(days)

    days_since_sunday = (first_date.weekday() + 1) % 7
    grid_start = first_date - timedelta(days=days_since_sunday)

    days_until_saturday = (5 - last_date.weekday()) % 7
    grid_end = last_date + timedelta(days=days_until_saturday)

    return grid_start, grid_end


def animation_markup(
    delay: float,
    static: bool,
) -> str:
    if static:
        return ""

    return f"""
      <animate
        attributeName="opacity"
        from="0"
        to="1"
        begin="{delay:.3f}s"
        dur="0.35s"
        fill="freeze"
      />
      <animateTransform
        attributeName="transform"
        type="translate"
        from="0 9"
        to="0 0"
        begin="{delay:.3f}s"
        dur="0.35s"
        fill="freeze"
      />
    """


def build_svg(data: dict, static: bool = False) -> str:
    days = parse_days(data)

    if not days:
        raise ValueError("No contribution days are available.")

    grid_start, grid_end = get_grid_dates(days)

    total_days = (grid_end - grid_start).days + 1
    total_weeks = total_days // 7

    current_streak, longest_streak = calculate_streaks(days)
    best_date, best_count = find_best_day(days)

    total_contributions = sum(
        day["count"]
        for day in days.values()
    )

    best_day_text = (
        f"{best_count} on {best_date.strftime('%b %d')}"
        if best_date
        else "0"
    )

    elements: list[str] = []

    elements.append(
        f"""<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{WIDTH}"
  height="{HEIGHT}"
  viewBox="0 0 {WIDTH} {HEIGHT}"
  role="img"
  aria-labelledby="title description"
>
  <title id="title">GitHub contribution heatmap for netbyme</title>
  <desc id="description">
    Animated GitHub contribution calendar showing daily activity,
    total contributions, streaks, and best contribution day.
  </desc>

  <rect
    width="{WIDTH}"
    height="{HEIGHT}"
    rx="14"
    fill="{BACKGROUND}"
  />

  <rect
    x="1"
    y="1"
    width="{WIDTH - 2}"
    height="{HEIGHT - 2}"
    rx="13"
    fill="{PANEL}"
    stroke="{BORDER}"
    stroke-width="2"
  />

  <text
    x="24"
    y="29"
    fill="{TEXT}"
    font-family="{FONT_FAMILY}"
    font-size="14"
    font-weight="700"
  >
    Contribution activity
  </text>

  <text
    x="{WIDTH - 24}"
    y="29"
    text-anchor="end"
    fill="{MUTED}"
    font-family="{FONT_FAMILY}"
    font-size="11"
  >
    {escape(str(data.get("username", "netbyme")))}
  </text>
"""
    )

    weekday_labels = {
        1: "Mon",
        3: "Wed",
        5: "Fri",
    }

    for row, label in weekday_labels.items():
        y = GRID_TOP + row * CELL_STEP + 9

        elements.append(
            f"""
  <text
    x="14"
    y="{y}"
    fill="{MUTED}"
    font-family="{FONT_FAMILY}"
    font-size="9"
  >
    {label}
  </text>
"""
        )

    shown_months: set[tuple[int, int]] = set()
    last_month_x = -100

    for week_index in range(total_weeks):
        week_date = grid_start + timedelta(days=week_index * 7)
        month_key = (week_date.year, week_date.month)
        x = GRID_LEFT + week_index * CELL_STEP

        if month_key not in shown_months and x - last_month_x >= 34:
            shown_months.add(month_key)
            last_month_x = x

            elements.append(
                f"""
  <text
    x="{x}"
    y="{GRID_TOP - 10}"
    fill="{MUTED}"
    font-family="{FONT_FAMILY}"
    font-size="9"
  >
    {week_date.strftime("%b")}
  </text>
"""
            )

    for week_index in range(total_weeks):
        for day_index in range(7):
            current_date = (
                grid_start
                + timedelta(days=week_index * 7 + day_index)
            )

            x = GRID_LEFT + week_index * CELL_STEP
            y = GRID_TOP + day_index * CELL_STEP

            contribution = days.get(
                current_date,
                {"count": 0, "level": 0},
            )

            count = contribution["count"]
            level = contribution["level"]
            fill = PALETTE[level]

            delay = 0.08 + (week_index + day_index) * 0.012
            opacity = "1" if static else "0"

            tooltip = (
                f"{count} contribution"
                if count == 1
                else f"{count} contributions"
            )

            elements.append(
                f"""
  <g opacity="{opacity}">
    <rect
      x="{x}"
      y="{y}"
      width="{CELL_SIZE}"
      height="{CELL_SIZE}"
      rx="2.5"
      fill="{fill}"
    >
      <title>
        {tooltip} on {current_date.strftime("%B %d, %Y")}
      </title>
    </rect>
    {animation_markup(delay, static)}
  </g>
"""
            )

    legend_x = WIDTH - 166
    legend_y = 171

    elements.append(
        f"""
  <text
    x="{legend_x - 34}"
    y="{legend_y + 9}"
    fill="{MUTED}"
    font-family="{FONT_FAMILY}"
    font-size="9"
  >
    Less
  </text>
"""
    )

    for level in range(5):
        x = legend_x + level * CELL_STEP

        elements.append(
            f"""
  <rect
    x="{x}"
    y="{legend_y}"
    width="{CELL_SIZE}"
    height="{CELL_SIZE}"
    rx="2.5"
    fill="{PALETTE[level]}"
  />
"""
        )

    elements.append(
        f"""
  <text
    x="{legend_x + 5 * CELL_STEP + 3}"
    y="{legend_y + 9}"
    fill="{MUTED}"
    font-family="{FONT_FAMILY}"
    font-size="9"
  >
    More
  </text>

  <line
    x1="24"
    y1="193"
    x2="{WIDTH - 24}"
    y2="193"
    stroke="{BORDER}"
  />

  <text
    x="24"
    y="213"
    fill="{BLUE}"
    font-family="{FONT_FAMILY}"
    font-size="10"
    font-weight="700"
  >
    total
  </text>

  <text
    x="64"
    y="213"
    fill="{TEXT}"
    font-family="{FONT_FAMILY}"
    font-size="10"
  >
    {total_contributions}
  </text>

  <text
    x="175"
    y="213"
    fill="{BLUE}"
    font-family="{FONT_FAMILY}"
    font-size="10"
    font-weight="700"
  >
    current streak
  </text>

  <text
    x="268"
    y="213"
    fill="{TEXT}"
    font-family="{FONT_FAMILY}"
    font-size="10"
  >
    {current_streak} days
  </text>

  <text
    x="375"
    y="213"
    fill="{BLUE}"
    font-family="{FONT_FAMILY}"
    font-size="10"
    font-weight="700"
  >
    longest streak
  </text>

  <text
    x="468"
    y="213"
    fill="{TEXT}"
    font-family="{FONT_FAMILY}"
    font-size="10"
  >
    {longest_streak} days
  </text>

  <text
    x="585"
    y="213"
    fill="{BLUE}"
    font-family="{FONT_FAMILY}"
    font-size="10"
    font-weight="700"
  >
    best day
  </text>

  <text
    x="642"
    y="213"
    fill="{TEXT}"
    font-family="{FONT_FAMILY}"
    font-size="10"
  >
    {escape(best_day_text)}
  </text>
</svg>
"""
    )

    return "\n".join(elements)


def main() -> None:
    static = os.getenv("STATIC") == "1"

    data = load_data()
    svg = build_svg(data, static)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")

    mode = "static" if static else "animated"

    print(f"Created {mode} contribution heatmap:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()