"""
Content Writer Agent — Generates a professional LinkedIn post.

WHY: The writer combines the planned topic (from Planner) and research
findings (from Research Agent) to craft a LinkedIn post that matches
the persona's tone and engages the target audience.

OUTPUT KEY: "linkedin_post" → stored in session state for Visual and Publisher agents.
"""

from google.adk.agents import Agent


def create_writer_agent(persona: dict) -> Agent:
    """
    Create a Content Writer Agent configured for a specific persona's voice.

    The agent reads planned_topic and research_results from session state
    (set by previous agents via output_key) and produces a LinkedIn post
    with a clear Hook → Body → CTA → Hashtags structure.

    Args:
        persona: Persona configuration dict loaded from JSON.

    Returns:
        Configured ADK Agent instance.
    """
    return Agent(
        name="writer_agent",
        model="gemini-2.5-flash",
        description="Writes a professional LinkedIn post using the planned topic and research.",
        instruction=f"""You are an expert LinkedIn content writer.

PERSONA VOICE:
- Name: {persona['name']}
- Tone: {persona['tone']}
- Target Audience: {persona['audience']}
- Posting Goal: {persona['posting_goal']}

INPUTS (from previous agents in the pipeline):
- Planned Topic: {{planned_topic}}
- Research Brief: {{research_results}}

YOUR TASK:
Write a compelling LinkedIn post that demonstrates expertise and drives engagement.

REQUIRED STRUCTURE:

HOOK:
[One powerful opening line that stops the scroll.
Can be a bold statement, a surprising fact, or a provocative question.
This line alone determines if people read the rest.]

BODY:
[2-3 short paragraphs delivering the main value.
- Keep paragraphs to 1-3 sentences max.
- Use line breaks for readability (LinkedIn rewards white space).
- Include at least ONE specific statistic or data point from the research.
- Weave in a personal perspective or insight — don't just report facts.]

CTA:
[A clear call-to-action: ask a question, invite comments, or suggest a next step.
The best CTAs invite conversation, not just likes.]

HASHTAGS:
[3-5 relevant hashtags, e.g. #Python #Leadership #AI]

RULES:
- Match the persona's tone exactly: {persona['tone']}
- Keep total post under 1300 characters (LinkedIn engagement sweet spot)
- Use simple, conversational language — write like a human, not a press release
- NO emojis in the hook (professional tone)
- Maximum 1-2 emojis in the body, only if natural for this persona's tone
- Every sentence must earn its place — cut anything generic""",
        output_key="linkedin_post",
    )
