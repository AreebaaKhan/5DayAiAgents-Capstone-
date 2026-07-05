"""
Research tools — core logic for the MCP research server.

WHY: The Research Agent communicates with these tools EXCLUSIVELY through
MCP (Model Context Protocol), demonstrating a clean tool-use boundary.
No direct Python imports of these functions exist in any agent code.

SEARCH STRATEGY:
  1. If SERPER_API_KEY is set → uses Serper.dev REST API for real web search
  2. Otherwise → uses FREE DuckDuckGo HTML search (no API key needed)
  3. If both fail → returns realistic mock data, clearly labeled as fallback

The DuckDuckGo fallback ensures the pipeline ALWAYS has real, live search
results, even without any API keys configured.
"""

import json
import os
import re
import html as html_module
from datetime import datetime
from typing import Optional
from urllib.parse import unquote


# ── Real search helper (Serper.dev) ───────────────────────────────────

def _get_serper_results(query: str, num_results: int = 5) -> Optional[list[dict]]:
    """
    Attempt a real web search via the Serper.dev REST API.

    Returns None if the API key is missing, requests is unavailable,
    or the API call fails — so callers can fall back to DuckDuckGo or mock data.
    """
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return None

    try:
        import requests  # imported here so the module loads even without requests
    except ImportError:
        return None

    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num_results},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
            }
            for item in data.get("organic", [])[:num_results]
        ]
    except Exception:
        # Any failure → return None so caller falls back
        return None


# ── Free search helper (DuckDuckGo HTML — no API key needed) ─────────

def _get_ddg_results(query: str, num_results: int = 5) -> Optional[list[dict]]:
    """
    Perform a free web search using DuckDuckGo's HTML endpoint.

    This requires NO API key and works out of the box. Results are parsed
    from the HTML response using regex. Returns None only on network failure.
    """
    try:
        import requests
    except ImportError:
        return None

    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            )
        }
        params = {"q": query}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        raw_html = resp.text

        # Split by result divs
        divs = re.split(
            r'<div[^>]*class="[^"]*web-result[^"]*"[^>]*>', raw_html
        )

        results = []
        for div in divs[1:]:
            title_match = re.search(
                r'<a\s+[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                div, re.DOTALL,
            )
            snippet_match = re.search(
                r'<a\s+[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                div, re.DOTALL,
            )

            if title_match:
                href = title_match.group(1)
                title = re.sub(r'<[^>]+>', '', title_match.group(2)).strip()
                title = html_module.unescape(title)

                # Extract clean URL from DDG redirect
                if "uddg=" in href:
                    actual_url = unquote(href.split("uddg=")[1].split("&")[0])
                else:
                    actual_url = href
                if actual_url.startswith("//"):
                    actual_url = "https:" + actual_url

                snippet = ""
                if snippet_match:
                    snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                    snippet = html_module.unescape(snippet)

                results.append({
                    "title": title,
                    "snippet": snippet,
                    "link": actual_url,
                })

                if len(results) >= num_results:
                    break

        return results if results else None
    except Exception:
        return None


# ── Unified search helper ─────────────────────────────────────────────

def _search_web(query: str, num_results: int = 5) -> tuple[Optional[list[dict]], str]:
    """
    Try Serper first, then DuckDuckGo, then return None.
    Returns (results, source_label).
    """
    serper = _get_serper_results(query, num_results)
    if serper:
        return serper, "serper_api"

    ddg = _get_ddg_results(query, num_results)
    if ddg:
        return ddg, "duckduckgo_free"

    return None, "mock_fallback"


# ── MCP Tool: search_trends ──────────────────────────────────────────

def search_trends(topic: str, niche: str) -> str:
    """
    Search for current trends related to a topic within a specific niche.
    Returns trending themes, discussions, and emerging patterns.

    Args:
        topic: The content topic to research trends for.
        niche: The industry or niche context.

    Returns:
        JSON string with trending information.
    """
    query = f"{topic} {niche} trends 2026"
    results, source = _search_web(query)

    if results:
        return json.dumps({
            "source": f"live_search ({source})",
            "query": query,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "results": results,
            "note": f"Real search results via {source}",
        }, indent=2)

    # ── Fallback: realistic mock data ─────────────────────────────
    return json.dumps({
        "source": "mock_fallback",
        "note": (
            "MOCK DATA — Both Serper and DuckDuckGo search failed. "
            "Using realistic fallback data."
        ),
        "query": query,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "trends": [
            {
                "trend": f"AI-powered automation in {niche}",
                "description": (
                    f"Companies in {niche} are increasingly adopting AI agents "
                    f"for content creation and strategic planning."
                ),
                "relevance": "high",
            },
            {
                "trend": f"Community-driven growth in {niche}",
                "description": (
                    "Building engaged communities is outperforming "
                    "traditional marketing approaches on LinkedIn."
                ),
                "relevance": "high",
            },
            {
                "trend": f"Short-form educational content about {topic}",
                "description": (
                    "Bite-sized, actionable tips are generating the "
                    "highest engagement on LinkedIn in 2026."
                ),
                "relevance": "medium",
            },
        ],
    }, indent=2)


# ── MCP Tool: search_statistics ──────────────────────────────────────

def search_statistics(topic: str) -> str:
    """
    Search for relevant statistics and data points about a topic.
    Returns quantitative data that can strengthen content credibility.

    Args:
        topic: The topic to find statistics for.

    Returns:
        JSON string with statistics and data points.
    """
    query = f"{topic} statistics data 2026"
    results, source = _search_web(query)

    if results:
        return json.dumps({
            "source": f"live_search ({source})",
            "query": query,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "results": results,
            "note": f"Real search results via {source}",
        }, indent=2)

    return json.dumps({
        "source": "mock_fallback",
        "note": (
            "MOCK DATA — Both Serper and DuckDuckGo search failed. "
            "Using realistic fallback data."
        ),
        "query": f"{topic} statistics 2026",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "statistics": [
            {
                "stat": "73% of professionals",
                "context": (
                    f"say that {topic} has significantly impacted "
                    f"their workflow in 2026"
                ),
                "source_note": "Mock — Industry Survey 2026",
            },
            {
                "stat": "2.4x increase",
                "context": (
                    f"in LinkedIn engagement for posts about {topic} "
                    f"compared to last year"
                ),
                "source_note": "Mock — LinkedIn Analytics Report",
            },
            {
                "stat": "58% of companies",
                "context": (
                    f"plan to increase investment in {topic} "
                    f"over the next 12 months"
                ),
                "source_note": "Mock — Market Research Report",
            },
        ],
    }, indent=2)


# ── MCP Tool: search_competitor_content ──────────────────────────────

def search_competitor_content(niche: str) -> str:
    """
    Search for what competitors and thought leaders are posting in a niche.
    Returns content themes and engagement patterns.

    Args:
        niche: The industry niche to analyze competitor content for.

    Returns:
        JSON string with competitor content analysis.
    """
    query = f"{niche} LinkedIn thought leaders content 2026"
    results, source = _search_web(query)

    if results:
        return json.dumps({
            "source": f"live_search ({source})",
            "query": query,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "results": results,
            "note": f"Real search results via {source}",
        }, indent=2)

    return json.dumps({
        "source": "mock_fallback",
        "note": (
            "MOCK DATA — Both Serper and DuckDuckGo search failed. "
            "Using realistic fallback data."
        ),
        "query": f"{niche} competitor content analysis",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "competitor_themes": [
            {
                "theme": "Personal storytelling with lessons",
                "engagement_level": "very high",
                "example": (
                    f"Top {niche} voices are sharing vulnerable stories "
                    f"about failures and comebacks"
                ),
            },
            {
                "theme": "Contrarian takes on industry norms",
                "engagement_level": "high",
                "example": (
                    f"Posts challenging conventional wisdom in {niche} "
                    f"generate strong debate and engagement"
                ),
            },
            {
                "theme": "Step-by-step tutorials and frameworks",
                "engagement_level": "high",
                "example": (
                    "Actionable how-to content with clear frameworks "
                    "performs consistently well"
                ),
            },
        ],
        "content_gaps": [
            f"Few creators in {niche} combine data with personal narrative",
            "Video and carousel content is underutilized compared to text posts",
        ],
    }, indent=2)
