#!/usr/bin/env python3
"""
Fetch citation counts from Google Scholar Author Profile via SerpApi and update index.html.

This script fetches the author's profile, extracts the citations for each paper,
and updates the corresponding `<span class="citation-badge">` elements.

Usage:
    SERPAPI_KEY=your_key python scripts/update_citations.py
"""

import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

# Path to the HTML file (relative to the repo root)
HTML_PATH = Path(__file__).parent.parent / "index.html"

# Mapping: span id  ->  substring of paper title to match from the profile
# We use lowercase substrings to make matching robust against minor formatting differences
PAPERS = {
    "cite-agentexpt": "agentexpt: automating ai experiment design",
    "cite-agentswift": "agentswift: efficient llm agent design",
    "cite-agentsquare": "agentsquare: automatic llm agent search",
    "cite-largereasoningmodels": "towards large reasoning models: a survey",
    "cite-autosota": "autosota: an end-to-end automated research system",
    "cite-synergy": "synergy-of-thoughts: eliciting efficient reasoning",
    "cite-agentsociety": "agentsociety challenge: designing llm agents",
    "cite-omniscientist": "omniscientist: toward a co-evolving ecosystem",
    "cite-aiagentbehavioral": "ai agent behavioral science",
}

AUTHOR_ID = "Ba-L9PYAAAAJ"


def fetch_author_citations(api_key: str) -> dict[str, int]:
    """Fetch the author profile using SerpApi and extract citations into a mapping."""
    params = {
        "engine": "google_scholar_author",
        "author_id": AUTHOR_ID,
        "api_key": api_key,
        "hl": "en"
    }

    print(f"Fetching Google Scholar profile for author_id: {AUTHOR_ID}...")
    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        print(f"  [ERROR] SerpApi returned an error: {results['error']}")
        sys.exit(1)

    articles = results.get("articles", [])
    print(f"  [OK] Fetched {len(articles)} articles from profile.")
    
    citation_map = {}
    for article in articles:
        title = article.get("title", "")
        # cited_by is a dictionary like {"value": 15, "link": "..."}
        citations = article.get("cited_by", {}).get("value", 0)
        citation_map[title] = citations
        
    return citation_map


def update_html(author_citations: dict[str, int]) -> bool:
    """
    Rewrite HTML_PATH with updated citation badges.
    Returns True if any change was made.
    """
    html = HTML_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    changed = False

    # Match predefined papers with the fetched profile data
    for span_id, title_substring in PAPERS.items():
        span = soup.find("span", id=span_id)
        if span is None:
            print(f"  [WARN] <span id='{span_id}'> not found in HTML.")
            continue

        # Find the matching paper in the author_citations dictionary
        matched_count = None
        matched_title = None
        for fetched_title, count in author_citations.items():
            if title_substring.lower() in fetched_title.lower():
                matched_count = count
                matched_title = fetched_title
                break
        
        if matched_count is None:
            print(f"  [WARN] Paper matching '{title_substring}' not found in fetched profile.")
            continue

        print(f"  [HTML] Updating '{matched_title[:50]}...' -> {matched_count} citations")
        
        # Link to the paper's citations on Google Scholar if it has citations, 
        # otherwise link to the author's profile
        if matched_count > 0:
            scholar_url = f"https://scholar.google.com/scholar?cites=&q={matched_title.replace(' ', '+')}"
        else:
            scholar_url = f"https://scholar.google.com/citations?user={AUTHOR_ID}"

        new_text = f"Cited by {matched_count}"

        # Rebuild the inner anchor
        a_tag = soup.new_tag("a", href=scholar_url, target="_blank")
        a_tag.string = new_text

        # Check if anything changed
        existing_a = span.find("a")
        if existing_a and existing_a.get_text(strip=True) == new_text:
            continue

        span.clear()
        span.append(a_tag)
        changed = True
        print(f"    -> Changed #{span_id} to '{new_text}'")

    if changed:
        HTML_PATH.write_text(str(soup), encoding="utf-8")
        print(f"\nSaved updated HTML to {HTML_PATH}")
    else:
        print("\nNo citation counts changed; HTML not modified.")

    return changed


def main() -> None:
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("Error: SERPAPI_KEY environment variable is not set.")
        sys.exit(1)

    print("=== Updating citation counts via SerpApi ===\n")
    
    author_citations = fetch_author_citations(api_key)
    
    print("\n=== Updating HTML ===\n")
    update_html(author_citations)
    print("\nDone.")


if __name__ == "__main__":
    main()
