"""
Planner Agent — Decides today's content topic based on the persona profile.

WHY: In a multi-agent content strategy system, the first step is deciding
WHAT to talk about. This agent analyzes the persona's niche, audience,
and goals to select a timely, relevant topic. Its reasoning is explicitly
requested and preserved so judges can see the agent's thought process.

OUTPUT KEY: "planned_topic" → stored in session state for downstream agents.
"""

from datetime import datetime
from google.adk.agents import Agent
from utils.model_config import get_model_name


# ── Tool: get_current_date ────────────────────────────────────────────
# WHY: The Planner needs to know today's date to pick timely content
# (e.g., Monday motivation, Friday roundups, seasonal themes).

def get_current_date() -> dict:
    """
    Returns the current date and day of the week.

    The planner uses this to make time-aware topic decisions —
    for example, choosing reflective content on Fridays or
    action-oriented content on Mondays.

    Returns:
        dict with date, day_of_week, month, and year.
    """
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "day_of_week": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": now.strftime("%Y"),
    }


def create_planner_agent(persona: dict) -> Agent:
    """
    Create a Planner Agent configured for a specific persona.

    The agent's instruction is dynamically built from the persona profile,
    ensuring topic selection aligns with the brand's voice and goals.

    Args:
        persona: Persona configuration dict loaded from JSON.

    Returns:
        Configured ADK Agent instance.
    """
    # Build comma-separated topic list for the instruction
    example_topics = ", ".join(persona.get("example_topics", []))

    # Check if the user has specified a target topic
    target_topic = persona.get("target_topic", "").strip()

    if target_topic:
        # User specified a topic — plan around it
        topic_instruction = f"""YOUR TASK:
1. Use the get_current_date tool to know today's date and day of week.
2. The user has requested a specific topic: "{target_topic}"
3. Your job is to REFINE and ANGLE this topic for maximum LinkedIn engagement.
4. Consider the persona's niche, audience, and goals to find the best angle.
5. Explain your reasoning in detail.

OUTPUT FORMAT (follow this structure exactly):

TOPIC: [Refined version of "{target_topic}" — make it specific and engaging]

REASONING:
- Why this angle of the topic will resonate with the target audience
- How it aligns with the persona's posting goals
- Why today (day of week, timeliness) is right for this topic
- What makes this angle likely to drive engagement

Do NOT write the actual post. Only decide the angle and explain why."""
    else:
        # No user topic — generate one from the persona profile
        topic_instruction = f"""YOUR TASK:
1. Use the get_current_date tool to know today's date and day of week.
2. Consider the persona's niche, audience, and goals.
3. Choose ONE specific topic for today's LinkedIn post.
4. Explain your reasoning in detail.

OUTPUT FORMAT (follow this structure exactly):

TOPIC: [Your chosen topic — be specific, not generic]

REASONING:
- Why this topic matters to the target audience right now
- How it aligns with the persona's posting goals
- Why today (day of week, timeliness) is right for this topic
- What makes this topic likely to drive engagement

Do NOT write the actual post. Only decide the topic and explain why."""

    return Agent(
        name="planner_agent",
        model=get_model_name(),
        description="Decides today's content topic based on the persona profile and current context.",
        instruction=f"""You are a strategic content planner for a brand persona.

PERSONA PROFILE:
- Name: {persona['name']}
- Niche: {persona['niche']}
- Tone: {persona['tone']}
- Target Audience: {persona['audience']}
- Posting Goal: {persona['posting_goal']}
- Posting Frequency: {persona['posting_frequency']}
- Example Topics: {example_topics}

{topic_instruction}""",
        tools=[get_current_date],
        output_key="planned_topic",
    )
