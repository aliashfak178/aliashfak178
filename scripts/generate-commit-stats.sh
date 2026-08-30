#!/usr/bin/env bash
set -euo pipefail

USERNAME="${1:-aliashfak178}"
OUTPUT="${2:-assets/commit-stats.svg}"
TOKEN="${GITHUB_TOKEN:?GITHUB_TOKEN is required}"

count_commits() {
  local since="$1"
  local query="author:${USERNAME}+committer-date:>=${since}"
  local encoded
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''${query}'''))")

  curl -sS \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/search/commits?q=${encoded}&per_page=1" \
    | jq -r '.total_count // 0'
}

today=$(date -u +%F)
week_start=$(date -u -d "monday this week" +%F)
month_start=$(date -u +%Y-%m-01)
year_start=$(date -u +%Y-01-01)
updated=$(date -u +"%Y-%m-%d %H:%M UTC")

echo "Fetching commit counts for ${USERNAME}..."
today_count=$(count_commits "${today}")
week_count=$(count_commits "${week_start}")
month_count=$(count_commits "${month_start}")
year_count=$(count_commits "${year_start}")

mkdir -p "$(dirname "${OUTPUT}")"

cat > "${OUTPUT}" <<SVG
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="160" viewBox="0 0 900 160">
  <rect width="900" height="160" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="450" y="28" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#667eea">COMMIT ACTIVITY</text>
  <text x="450" y="48" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#8b949e">Updated ${updated}</text>

  <rect x="30"  y="65" width="190" height="75" rx="10" fill="#161b22" stroke="#667eea" stroke-width="1"/>
  <rect x="245" y="65" width="190" height="75" rx="10" fill="#161b22" stroke="#764ba2" stroke-width="1"/>
  <rect x="460" y="65" width="190" height="75" rx="10" fill="#161b22" stroke="#f093fb" stroke-width="1"/>
  <rect x="675" y="65" width="190" height="75" rx="10" fill="#161b22" stroke="#00A1E0" stroke-width="1"/>

  <text x="125" y="92" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#8b949e">TODAY</text>
  <text x="340" y="92" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#8b949e">THIS WEEK</text>
  <text x="555" y="92" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#8b949e">THIS MONTH</text>
  <text x="770" y="92" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#8b949e">THIS YEAR</text>

  <text x="125" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#667eea">${today_count}</text>
  <text x="340" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#764ba2">${week_count}</text>
  <text x="555" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#f093fb">${month_count}</text>
  <text x="770" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#00A1E0">${year_count}</text>
</svg>
SVG

echo "Generated ${OUTPUT}"
echo "Today: ${today_count} | Week: ${week_count} | Month: ${month_count} | Year: ${year_count}"
