"""Local demo fallback for the content pipeline.

When Gemini quota is exhausted, the Streamlit app uses live DuckDuckGo
search and dynamic templates to generate high-quality content.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.publisher_agent import simulate_publish
from agents.visual_agent import generate_infographic
from mcp_server.tools import (
    search_competitor_content,
    search_statistics,
    search_trends,
)
from utils.output_saver import save_agent_output


def _pick_topic(persona: dict[str, Any]) -> str:
    target = persona.get("target_topic", "").strip()
    if target:
        return target
    example_topics = persona.get("example_topics") or []
    if example_topics:
        return str(example_topics[0])
    return f"{persona.get('niche', 'Content Strategy')} Growth Strategies"


def _topic_reasoning(persona: dict[str, Any], topic: str) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    return (
        f"TOPIC: {topic}\n\n"
        "REASONING:\n"
        f"- Aligns with the persona's niche: {persona.get('niche', 'N/A')}\n"
        f"- Speaks directly to: {persona.get('audience', 'N/A')}\n"
        f"- Timely for {today} and supports the posting goal\n"
        "- Specific enough to create actionable, engaging content"
    )


def _extract_insights(search_json: str, max_items: int = 3) -> list[str]:
    """Pull short, clean insight sentences from search JSON."""
    try:
        data = json.loads(search_json)
    except (json.JSONDecodeError, TypeError):
        return []

    insights = []

    for result in data.get("results", []):
        snippet = result.get("snippet", "").strip()
        if snippet and len(snippet) > 30:
            # Take first sentence, clean it up
            sentence = snippet.split(".")[0].strip()
            if len(sentence) > 20:
                # Ensure it doesn't end mid-word
                if len(sentence) > 100:
                    sentence = sentence[:100].rsplit(" ", 1)[0]
                insights.append(sentence)
                if len(insights) >= max_items:
                    return insights

    return insights


def _clean_hashtag(word: str) -> str:
    """Make a clean hashtag from a word — alphanumeric only."""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', word)
    return cleaned[:20] if cleaned else ""


def _build_post(persona: dict[str, Any], topic: str, trends_json: str, stats_json: str) -> str:
    """Build a polished LinkedIn post using real search data."""
    name = persona.get("name", "Content Creator")
    niche = persona.get("niche", "your industry")

    # Simplify audience for use in text
    audience_full = persona.get("audience", "professionals")
    audience_short = audience_full.split(",")[0].strip()

    # Extract real insights from search
    trend_insights = _extract_insights(trends_json, 2)
    stat_insights  = _extract_insights(stats_json, 1)

    # ── Hook ──────────────────────────────────────────────────────
    hook = f"Most {audience_short} overlook this about {topic.lower()} — and it's costing them."

    # ── Body ──────────────────────────────────────────────────────
    body_parts = []

    if trend_insights:
        body_parts.append(
            f"Here's what the latest research shows:\n"
            f"{trend_insights[0]}."
        )
    else:
        body_parts.append(
            f"The conversation around {topic.lower()} in {niche} is shifting fast."
        )

    if len(trend_insights) > 1:
        body_parts.append(f"There's another pattern emerging: {trend_insights[1]}.")

    if stat_insights:
        body_parts.append(f"The data backs it up — {stat_insights[0]}.")
    else:
        body_parts.append(
            f"Industry data shows this trend is accelerating, "
            f"especially for {audience_short}."
        )

    body_parts.append(
        f"If you're in {niche}, this isn't noise — it's a signal worth acting on."
    )

    body = "\n\n".join(body_parts)

    # ── CTA ───────────────────────────────────────────────────────
    cta = f"What's your experience with {topic.lower()}? I'd love to hear your take 👇"

    # ── Hashtags — clean, no special chars ─────────────────────────
    niche_tag = _clean_hashtag(niche.split()[0]) if niche.split() else "Business"
    topic_words = topic.split()
    topic_tag = _clean_hashtag(topic_words[0]) if topic_words else "Strategy"
    topic_tag2 = _clean_hashtag(topic_words[-1]) if len(topic_words) > 1 else "Growth"

    hashtags = f"#{niche_tag} #{topic_tag} #{topic_tag2} #LinkedIn #ContentStrategy"

    return (
        f"HOOK:\n{hook}\n\n"
        f"BODY:\n{body}\n\n"
        f"CTA:\n{cta}\n\n"
        f"HASHTAGS:\n{hashtags}"
    )


def run_demo_fallback(persona: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Run a fully local demo pipeline with live search and dynamic content."""
    topic = _pick_topic(persona)
    planned_topic = _topic_reasoning(persona, topic)
    niche = persona.get("niche", "")

    # Fetch search results (DuckDuckGo — no API key needed)
    trends = search_trends(topic, niche)
    stats = search_statistics(topic)
    competitor = search_competitor_content(niche)

    research_brief = (
        f"RESEARCH BRIEF FOR: {topic}\n\n"
        f"KEY TRENDS:\n{trends}\n\n"
        f"SUPPORTING DATA:\n{stats}\n\n"
        f"COMPETITOR INSIGHTS:\n{competitor}\n\n"
        "RECOMMENDED ANGLE:\n"
        f"Lead with data-driven insights about {topic}, "
        f"practical lessons, and a {persona.get('tone', 'professional')} tone.\n\n"
        "DATA SOURCE NOTE:\n"
        "Fallback mode — used live DuckDuckGo search (no API key required)."
    )

    linkedin_post = _build_post(persona, topic, trends, stats)

    # Build infographic key points from search insights
    all_insights = _extract_insights(trends, 2) + _extract_insights(stats, 1)
    if not all_insights or len(all_insights) < 2:
        all_insights = [
            f"{topic} is transforming {niche}",
            "Data-driven strategies outperform guesswork",
            "Consistency and trust compound over time",
            "Early adopters capture the most value",
        ]
    key_points = "\n".join(all_insights[:4])

    visual_result = generate_infographic(
        topic=topic,
        key_points=key_points,
        persona_name=persona.get("name", "Brand"),
    )
    image_path = visual_result.get("image_path") or "No image generated"

    publish_record = simulate_publish(linkedin_post, image_path)
    publish_result = (
        "Content has been reviewed and approved.\n"
        "LinkedIn post has been simulated (not published).\n\n"
        f"Status: {publish_record.get('status', 'SIMULATED_PUBLISH')}"
    )

    for agent_name, key, data in [
        ("planner_agent",   "planned_topic",   planned_topic),
        ("research_agent",  "research_results", research_brief),
        ("writer_agent",    "linkedin_post",    linkedin_post),
        ("visual_agent",    "image_path",       image_path),
        ("publisher_agent", "publish_result",   publish_result),
    ]:
        save_agent_output(
            agent_name=agent_name, run_id=run_id, output_data=data,
            metadata={"persona": persona.get("name", "Unknown"), "output_key": key, "mode": "demo_fallback"},
        )

    return {
        "run_id": run_id,
        "persona": persona.get("name", "Unknown"),
        "results": {
            "planner_agent": planned_topic,
            "research_agent": research_brief,
            "writer_agent": linkedin_post,
            "visual_agent": image_path,
            "publisher_agent": publish_result,
        },
        "final_response": "Demo fallback completed with live search data.",
        "fallback": True,
        "fallback_note": "Gemini quota exhausted — used DuckDuckGo live search and dynamic templates.",
    }