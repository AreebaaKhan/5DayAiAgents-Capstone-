"""
Pipeline Orchestrator — runs the multi-agent content strategy pipeline.

WHY: This is the heart of the system. It assembles all five agents into
an ADK SequentialAgent, creates a Runner + Session, and executes the
full pipeline: Planner → Research → Writer → Visual → Publisher.

ARCHITECTURE:
  SequentialAgent guarantees deterministic execution order.
  Session state (via output_key) automatically pipes data between agents.
  After the pipeline runs, all outputs are extracted and saved as JSON.

ADK CONCEPTS DEMONSTRATED:
  - SequentialAgent (workflow orchestration)
  - Runner + InMemorySessionService (programmatic execution)
  - Session state sharing between agents
  - output_key for automatic state management
"""

import asyncio
import json
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

# Suppress SequentialAgent deprecation warning — ADK 2.3.0 says to use
# "Workflow" but that class isn't importable yet. SequentialAgent works fine.
warnings.filterwarnings("ignore", message=".*SequentialAgent is deprecated.*")
warnings.filterwarnings("ignore", message=".*BaseAgentConfig is deprecated.*")

from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from agents.planner_agent import create_planner_agent
from agents.research_agent import create_research_agent
from agents.writer_agent import create_writer_agent
from agents.visual_agent import create_visual_agent
from agents.publisher_agent import create_publisher_agent
from utils.logger import AgentLogger, Colors
from utils.output_saver import save_agent_output

# Load environment variables from .env file
load_dotenv()


async def run_pipeline(persona: dict) -> dict[str, Any]:
    """
    Execute the full content strategy pipeline for a given persona.

    This function:
    1. Creates all 5 specialized agents (Planner, Research, Writer, Visual, Publisher)
    2. Assembles them into a SequentialAgent pipeline
    3. Runs the pipeline with a Runner + InMemorySessionService
    4. Extracts all outputs from session state
    5. Saves each output as structured JSON to outputs/<run_id>/

    Args:
        persona: Persona configuration dict loaded from a JSON file.

    Returns:
        dict with run_id, persona name, per-agent results, and final response.
    """
    # ── Generate a unique run ID ──────────────────────────────────────
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = AgentLogger(run_id)

    print(f"\n{'═' * 60}")
    print(f"🚀 AI Brand Content Strategist Pipeline")
    print(f"📋 Persona: {persona['name']}")
    print(f"🕐 Run ID:  {run_id}")
    print(f"{'═' * 60}")

    # ── Step 1: Create all agents ─────────────────────────────────────
    logger.log_agent_start(
        "pipeline_setup",
        f"Creating agents for persona: {persona['name']}",
    )

    try:
        planner = create_planner_agent(persona)
        researcher = create_research_agent()
        writer = create_writer_agent(persona)
        visual = create_visual_agent()
        publisher = create_publisher_agent()
        logger.log_agent_end("pipeline_setup", "All 5 agents created successfully")
    except Exception as e:
        logger.log_error("pipeline_setup", str(e))
        raise

    # ── Step 2: Assemble the SequentialAgent ──────────────────────────
    # WHY: SequentialAgent ensures deterministic, linear execution.
    # Each agent's output_key writes to session state, which the next
    # agent reads via {key_name} placeholders in its instruction.
    pipeline_agent = SequentialAgent(
        name="content_strategy_pipeline",
        sub_agents=[planner, researcher, writer, visual, publisher],
    )

    # ── Step 3: Create Runner and Session ─────────────────────────────
    # WHY: InMemorySessionService is lightweight and perfect for a demo.
    # The Runner manages the agent lifecycle and message routing.
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="brand_content_strategist",
        agent=pipeline_agent,
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="brand_content_strategist",
        user_id="content_creator",
    )

    # ── Step 4: Run the pipeline ──────────────────────────────────────
    # The initial message kicks off the SequentialAgent.
    # Each sub-agent processes in order, reading shared session state.
    initial_message = types.Content(
        role="user",
        parts=[types.Part(text=(
            f"Create today's LinkedIn content for the '{persona['name']}' persona. "
            f"Niche: {persona['niche']}. "
            f"Follow the full pipeline: plan topic → research → write post → "
            f"generate visual → get human approval → publish."
        ))],
    )

    logger.log_agent_start(
        "pipeline_execution",
        f"Running full pipeline for {persona['name']}",
    )

    final_response = None
    try:
        async for event in runner.run_async(
            session_id=session.id,
            user_id="content_creator",
            new_message=initial_message,
        ):
            # Capture the final response from the last agent in the pipeline
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text

    except Exception as e:
        logger.log_error("pipeline_execution", str(e))
        raise

    logger.log_agent_end("pipeline_execution", "Pipeline completed successfully")

    # ── Step 5: Extract and save outputs from session state ──────────
    # WHY: Each agent saved its output to session state via output_key.
    # We now extract these and save as structured JSON to outputs/<run_id>/
    # for judges to inspect intermediate results.
    current_session = await session_service.get_session(
        app_name="brand_content_strategist",
        user_id="content_creator",
        session_id=session.id,
    )

    state = current_session.state if current_session else {}

    # Map agent names to their output_key values
    output_keys = {
        "planner_agent": "planned_topic",
        "research_agent": "research_results",
        "writer_agent": "linkedin_post",
        "visual_agent": "image_path",
        "publisher_agent": "publish_result",
    }

    results: dict[str, Any] = {}
    for agent_name, key in output_keys.items():
        output = state.get(key, "No output captured")
        results[agent_name] = output

        # Persist each agent's output as structured JSON
        save_agent_output(
            agent_name=agent_name,
            run_id=run_id,
            output_data=output,
            metadata={
                "persona": persona["name"],
                "output_key": key,
            },
        )

    # ── Step 6: Log pipeline summary ─────────────────────────────────
    logger.log_pipeline_summary()

    return {
        "run_id": run_id,
        "persona": persona["name"],
        "results": results,
        "final_response": final_response,
    }
