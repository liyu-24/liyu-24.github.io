#!/usr/bin/env python3
"""
Fetch GitHub star counts and update index.html.

This script queries the GitHub REST API for configured repositories and updates
the corresponding `<span class="star-badge">` elements.

Usage:
    python scripts/update_github_stars.py
    GITHUB_TOKEN=xxx python scripts/update_github_stars.py
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

HTML_PATH = Path(__file__).parent.parent / "index.html"

# span id -> repository config
REPOS = {
    "star-autosota": {
        "repo": "tsinghua-fib-lab/AutoSOTA",
        "url": "https://github.com/tsinghua-fib-lab/AutoSOTA",
    },
}


def fetch_star_count(repo: str, token: str | None = None) -> int:
    """Fetch stargazers_count for a GitHub repository."""
    url = f"https://api.github.com/repos/{repo}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "liyu-24-github-io-star-updater",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"  [ERROR] GitHub API request failed for {repo}: {exc.code} {body}")
        sys.exit(1)

    if "stargazers_count" not in data:
        print(f"  [ERROR] Unexpected GitHub API response for {repo}: {data}")
        sys.exit(1)

    return data["stargazers_count"]


def update_html(star_counts: dict[str, int]) -> bool:
    """Rewrite HTML_PATH with updated star badges. Returns True if changed."""
    html = HTML_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    changed = False

    for span_id, count in star_counts.items():
        span = soup.find("span", id=span_id)
        if span is None:
            print(f"  [WARN] <span id='{span_id}'> not found in HTML.")
            continue

        repo_url = REPOS[span_id]["url"]
        new_text = f"⭐ {count} stars"

        existing_a = span.find("a")
        if existing_a and existing_a.get_text(strip=True) == new_text:
            print(f"  [SKIP] #{span_id} already shows '{new_text}'")
            continue

        a_tag = soup.new_tag("a", href=repo_url, target="_blank")
        a_tag.string = new_text
        span.clear()
        span.append(a_tag)
        changed = True
        print(f"  [HTML] Updated #{span_id} -> '{new_text}'")

    if changed:
        HTML_PATH.write_text(str(soup), encoding="utf-8")
        print(f"\nSaved updated HTML to {HTML_PATH}")
    else:
        print("\nNo star counts changed; HTML not modified.")

    return changed


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")

    print("=== Updating GitHub star counts ===\n")
    star_counts = {}
    for span_id, config in REPOS.items():
        repo = config["repo"]
        print(f"Fetching stars for {repo}...")
        count = fetch_star_count(repo, token)
        star_counts[span_id] = count
        print(f"  [OK] {repo}: {count} stars")

    print("\n=== Updating HTML ===\n")
    update_html(star_counts)
    print("\nDone.")


if __name__ == "__main__":
    main()
