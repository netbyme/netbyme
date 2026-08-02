
#!/usr/bin/env python3

import os
from pathlib import Path
from xml.sax.saxutils import escape


WIDTH = 490
HEIGHT = 370

OUTPUT_PATH = Path("assets/info-card.svg")

BACKGROUND = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
GREEN = "#39d353"
BLUE = "#58a6ff"
YELLOW = "#d29922"
RED = "#f85149"

FONT_FAMILY = (
    "JetBrains Mono, Cascadia Code, SFMono-Regular, "
    "Consolas, Liberation Mono, monospace"
)


PROFILE_ROWS = [
    ("role", "IT Support → Network Automation"),
    ("location", "Casablanca, Morocco"),
    ("focus", "CCNA · Python · Automation"),
    ("network", "Cisco IOS · VLAN · OSPF · IPv6"),
    ("automation", "Python · Netmiko · Git · Bash"),
    ("systems", "Linux · Windows · WSL"),
    ("projects", "3 production-style tools"),
    ("goal", "Network Automation Engineer"),
]


def animation_tags(delay: float, static: bool) -> str:
    if static:
        return ""

    return f"""
      <animate
        attributeName="opacity"
        from="0"
        to="1"
        begin="{delay:.2f}s"
        dur="0.35s"
        fill="freeze"
      />
      <animateTransform
        attributeName="transform"
        type="translate"
        from="14 0"
        to="0 0"
        begin="{delay:.2f}s"
        dur="0.35s"
        fill="freeze"
      />
    """


def animated_group(content: str, delay: float, static: bool) -> str:
    opacity = "1" if static else "0"

    return f"""
    <g opacity="{opacity}">
      {content}
      {animation_tags(delay, static)}
    </g>
    """


def create_svg(static: bool = False) -> str:
    elements: list[str] = []

    elements.append(
        f"""
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{WIDTH}"
  height="{HEIGHT}"
  viewBox="0 0 {WIDTH} {HEIGHT}"
  role="img"
  aria-labelledby="title description"
>
  <title id="title">Mohammed Hammouch network automation profile card</title>
  <desc id="description">
    Terminal-style profile information card showing current role,
    networking focus, tools, systems, projects, and career goal.
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

  <rect
    x="1"
    y="1"
    width="{WIDTH - 2}"
    height="40"
    rx="13"
    fill="{BACKGROUND}"
  />

  <path
    d="M1 28 Q1 41 14 41 H476 Q489 41 489 28 V41 H1 Z"
    fill="{BACKGROUND}"
  />

  <line
    x1="1"
    y1="41"
    x2="{WIDTH - 1}"
    y2="41"
    stroke="{BORDER}"
  />

  <circle cx="20" cy="21" r="5" fill="{RED}" />
  <circle cx="38" cy="21" r="5" fill="{YELLOW}" />
  <circle cx="56" cy="21" r="5" fill="{GREEN}" />

  <text
    x="245"
    y="26"
    text-anchor="middle"
    fill="{MUTED}"
    font-family="{FONT_FAMILY}"
    font-size="12"
  >
    netbyme@github: ~/profile
  </text>
"""
    )

    header = f"""
      <text
        x="26"
        y="76"
        fill="{GREEN}"
        font-family="{FONT_FAMILY}"
        font-size="20"
        font-weight="700"
      >
        mohammed@netbyme
      </text>

      <text
        x="26"
        y="99"
        fill="{MUTED}"
        font-family="{FONT_FAMILY}"
        font-size="13"
      >
        ─────────────────────────────────────────
      </text>

      <text
        x="26"
        y="123"
        fill="{TEXT}"
        font-family="{FONT_FAMILY}"
        font-size="15"
        font-weight="600"
      >
        Mohammed Hammouch
      </text>
"""

    elements.append(animated_group(header, 0.15, static))

    start_y = 153
    row_spacing = 25

    for index, (key, value) in enumerate(PROFILE_ROWS):
        y = start_y + index * row_spacing
        delay = 0.35 + index * 0.10

        row = f"""
          <text
            x="26"
            y="{y}"
            font-family="{FONT_FAMILY}"
            font-size="13"
          >
            <tspan fill="{BLUE}" font-weight="600">
              {escape(key):<11}
            </tspan>
            <tspan fill="{MUTED}">:</tspan>
            <tspan fill="{TEXT}" dx="8">
              {escape(value)}
            </tspan>
          </text>
        """

        elements.append(animated_group(row, delay, static))

    status_delay = 0.35 + len(PROFILE_ROWS) * 0.10 + 0.10

    status = f"""
      <line
        x1="26"
        y1="337"
        x2="464"
        y2="337"
        stroke="{BORDER}"
      />

      <circle
        cx="33"
        cy="354"
        r="4"
        fill="{GREEN}"
      />

      <text
        x="45"
        y="359"
        fill="{MUTED}"
        font-family="{FONT_FAMILY}"
        font-size="12"
      >
        building reliable network automation tools
      </text>
    """

    elements.append(animated_group(status, status_delay, static))

    elements.append("</svg>")

    return "\n".join(elements)


def main() -> None:
    static = os.getenv("STATIC") == "1"

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(create_svg(static), encoding="utf-8")

    mode = "static" if static else "animated"

    print(f"Created {mode} profile card:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()


