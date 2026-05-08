#!/usr/bin/env python3
"""
Fetch citation counts from Google Scholar and update index.html.

The script searches each paper by title on Google Scholar using the `scholarly`
library, then rewrites the inner text of the corresponding `<span class="citation-badge">`
elements to reflect the latest citation count.

Usage:
    python scripts/update_citations.py
"""

import re
import time
import random
from pathlib import Path

from scholarly import scholarly
from bs4 import BeautifulSoup

# Path to the HTML file (relative to the repo root)
HTML_PATH = Path(__file__).parent.parent / "index.html"

# Mapping: span id  ->  paper title to search on Google Scholar
PAPERS = {
    "cite-agentexpt": "AgentExpt: Automating AI Experiment Design with Resource Retrieval Agent",
    "cite-agentswift": "AgentSwift: Efficient LLM Agent Design via Value-guided Hierarchical Search",
    "cite-agentsquare": "AgentSquare: Automatic LLM Agent Search in Modular Design Space",
    "cite-largereasoningmodels": "Towards Large Reasoning Models: A Survey of Reinforced Reasoning with Large Language Models",
    "cite-autosota": "AutoSOTA: An End-to-End Automated Research System for State-of-the-Art AI Model Discovery",
    "cite-synergy": "Synergy-of-Thoughts: Eliciting Efficient Reasoning in Hybrid Language Models",
    "cite-agentsociety": "AgentSociety Challenge: Designing LLM Agents for User Modeling and Recommendation on Web Platforms",
    "cite-omniscientist": "OmniScientist: Toward a Co-evolving Ecosystem of Human and AI Scientists",
    "cite-aiagentbehavioral": "AI agent behavioral science",
}

# Google Scholar search URL template (used as the href for the badge link)
SCHOLAR_SEARCH_URL = "https://scholar.google.com/scholar?q={query}"


def fetch_citation_count(title: str) -> int | None:
    """Return the number of citations for *title* from Google Scholar, or None on failure."""
    try:
        search_query = scholarly.search_pubs(title)
        result = next(search_query, None)
        if result is None:
            print(f"  [WARN] No result found for: {title!r}")
            return None
        num_citations = result.get("num_citations", 0)
        print(f"  [OK] '{title[:60]}...' -> {num_citations} citations")
        return num_citations
    except Exception as exc:
        print(f"  [ERROR] Failed to fetch citations for {title!r}: {exc}")
        return None


def update_html(citations: dict[str, int | None]) -> bool:
    """
    Rewrite HTML_PATH with updated citation badges.
    Returns True if any change was made.
    """
    html = HTML_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    changed = False

    for span_id, count in citations.items():
        if count is None:
            continue
        span = soup.find("span", id=span_id)
        if span is None:
            print(f"  [WARN] <span id='{span_id}'> not found in HTML.")
            continue

        paper_title = PAPERS[span_id]
        scholar_url = SCHOLAR_SEARCH_URL.format(
            query=re.sub(r"\s+", "+", paper_title.strip())
        )
        new_text = f"Cited by {count}"

        # Rebuild the inner anchor
        a_tag = soup.new_tag("a", href=scholar_url, target="_blank")
        a_tag.string = new_text

        # Check if anything changed to avoid needless git commits
        existing_a = span.find("a")
        if existing_a and existing_a.get_text(strip=True) == new_text:
            continue

        span.clear()
        span.append(a_tag)
        changed = True
        print(f"  [HTML] Updated #{span_id} -> {new_text}")

    if changed:
        HTML_PATH.write_text(str(soup), encoding="utf-8")
        print(f"\nSaved updated HTML to {HTML_PATH}")
    else:
        print("\nNo citation counts changed; HTML not modified.")

    return changed


def main() -> None:
    print("=== Updating citation counts from Google Scholar ===\n")

    citations: dict[str, int | None] = {}
    for span_id, title in PAPERS.items():
        print(f"Fetching: {title[:70]}")
        count = fetch_citation_count(title)
        citations[span_id] = count
        # Be polite to Google Scholar – random sleep between requests
        time.sleep(random.uniform(3.0, 7.0))

    print("\n=== Updating HTML ===\n")
    update_html(citations)
    print("\nDone.")


if __name__ == "__main__":
    main()
