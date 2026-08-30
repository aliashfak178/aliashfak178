#!/usr/bin/env python3
"""Generate commit/activity stats panel for GitHub profile README."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from xml.sax.saxutils import escape

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None


USERNAME = sys.argv[1] if len(sys.argv) > 1 else "aliashfak178"
OUTPUT_SVG = sys.argv[2] if len(sys.argv) > 2 else "assets/commit-stats.svg"
OUTPUT_PNG = sys.argv[3] if len(sys.argv) > 3 else "assets/commit-stats.png"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def graphql_commit_count(from_iso: str, to_iso: str) -> int:
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
        }
      }
    }
    """
    payload = json.dumps(
        {
            "query": query,
            "variables": {"login": USERNAME, "from": from_iso, "to": to_iso},
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "commit-stats-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    collection = (
        data.get("data", {})
        .get("user", {})
        .get("contributionsCollection", {})
    )
    return int(collection.get("totalCommitContributions") or 0)


def fetch_contribution_map(year: int) -> dict[str, int]:
    url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y={year}"
    req = urllib.request.Request(url, headers={"User-Agent": "commit-stats-generator"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return {item["date"]: int(item["count"]) for item in data.get("contributions", [])}


def sum_contributions(by_date: dict[str, int], start: date, end: date) -> int:
    total = 0
    current = start
    while current <= end:
        total += by_date.get(current.isoformat(), 0)
        current += timedelta(days=1)
    return total


def counts_from_contributions_api() -> dict[str, int]:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    year_start = date(today.year, 1, 1)

    by_date = fetch_contribution_map(today.year)
    if today.year != year_start.year:
        by_date.update(fetch_contribution_map(year_start.year))

    return {
        "today": by_date.get(today.isoformat(), 0),
        "week": sum_contributions(by_date, week_start, today),
        "month": sum_contributions(by_date, month_start, today),
        "year": sum_contributions(by_date, year_start, today),
    }


def counts_from_graphql() -> dict[str, int]:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    year_start = date(today.year, 1, 1)
    to_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "today": graphql_commit_count(f"{today.isoformat()}T00:00:00Z", to_iso),
        "week": graphql_commit_count(f"{week_start.isoformat()}T00:00:00Z", to_iso),
        "month": graphql_commit_count(f"{month_start.isoformat()}T00:00:00Z", to_iso),
        "year": graphql_commit_count(f"{year_start.isoformat()}T00:00:00Z", to_iso),
    }


def get_counts() -> dict[str, int]:
    if TOKEN:
        try:
            counts = counts_from_graphql()
            if any(counts.values()):
                print("Using GraphQL commit counts")
                return counts
            print("GraphQL returned all zeros, using contributions API fallback")
        except Exception as exc:
            print(f"GraphQL failed ({exc}), using contributions API fallback")

    print("Using public contributions API")
    return counts_from_contributions_api()


def write_svg(counts: dict[str, int], updated: str) -> None:
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="160" viewBox="0 0 900 160">
  <rect width="900" height="160" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="450" y="28" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#667eea">COMMIT ACTIVITY</text>
  <text x="450" y="48" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#8b949e">Updated {escape(updated)}</text>
  <rect x="30"  y="65" width="190" height="75" rx="10" fill="#161b22" stroke="#667eea" stroke-width="1"/>
  <rect x="245" y="65" width="190" height="75" rx="10" fill="#161b22" stroke="#764ba2" stroke-width="1"/>
  <rect x="460" y="65" width="190" height="75" rx="10" fill="#161b22" stroke="#f093fb" stroke-width="1"/>
  <rect x="675" y="65" width="190" height="75" rx="10" fill="#161b22" stroke="#00A1E0" stroke-width="1"/>
  <text x="125" y="92" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#8b949e">TODAY</text>
  <text x="340" y="92" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#8b949e">THIS WEEK</text>
  <text x="555" y="92" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#8b949e">THIS MONTH</text>
  <text x="770" y="92" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#8b949e">THIS YEAR</text>
  <text x="125" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#667eea">{counts['today']}</text>
  <text x="340" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#764ba2">{counts['week']}</text>
  <text x="555" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#f093fb">{counts['month']}</text>
  <text x="770" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#00A1E0">{counts['year']}</text>
</svg>
"""
    os.makedirs(os.path.dirname(OUTPUT_SVG) or ".", exist_ok=True)
    with open(OUTPUT_SVG, "w", encoding="utf-8") as handle:
        handle.write(svg)


def write_png(counts: dict[str, int], updated: str) -> None:
    if Image is None:
        print("Pillow not installed, skipping PNG generation")
        return

    width, height = 900, 160
    img = Image.new("RGB", (width, height), "#0d1117")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 18)
        sub_font = ImageFont.truetype("arial.ttf", 11)
        label_font = ImageFont.truetype("arial.ttf", 12)
        num_font = ImageFont.truetype("arialbd.ttf", 30)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        num_font = ImageFont.load_default()

    draw.text((360, 12), "COMMIT ACTIVITY", fill="#667eea", font=title_font)
    draw.text((300, 36), f"Updated {updated}", fill="#8b949e", font=sub_font)

    boxes = [
        (30, "#667eea", "TODAY", counts["today"]),
        (245, "#764ba2", "THIS WEEK", counts["week"]),
        (460, "#f093fb", "THIS MONTH", counts["month"]),
        (675, "#00A1E0", "THIS YEAR", counts["year"]),
    ]

    for x, color, label, value in boxes:
        draw.rounded_rectangle((x, 65, x + 190, 140), radius=10, outline=color, width=1, fill="#161b22")
        draw.text((x + 95, 78), label, fill="#8b949e", font=label_font, anchor="mm")
        draw.text((x + 95, 118), str(value), fill=color, font=num_font, anchor="mm")

    os.makedirs(os.path.dirname(OUTPUT_PNG) or ".", exist_ok=True)
    img.save(OUTPUT_PNG, "PNG")


def main() -> None:
    counts = get_counts()
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    write_svg(counts, updated)
    write_png(counts, updated)
    print(
        f"Generated {OUTPUT_SVG} and {OUTPUT_PNG} | "
        f"Today={counts['today']} Week={counts['week']} "
        f"Month={counts['month']} Year={counts['year']}"
    )


if __name__ == "__main__":
    main()
