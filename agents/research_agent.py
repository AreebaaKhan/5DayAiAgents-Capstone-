"""
Research Agent — Gathers current facts and trends via MCP tools.

WHY: Good content needs supporting data. This agent communicates with
research tools EXCLUSIVELY through MCP (Model Context Protocol),
demonstrating a clean architectural boundary. The agent does NOT import
any Python functions directly — it discovers and calls tools through
the MCP protocol over stdio transport.

MCP BOUNDARY:
  Agent (this file)  ──stdio──▶  mcp_server/server.py  ──▶  tools.py
  The agent only knows about tool names and schemas via MCP discovery.

OUTPUT KEY: "research_results" → stored in session state for the Writer Agent.
"""

import os
import sys

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioConnectionParams,
    StdioServerParameters,
)
from utils.model_config import get_model_name


def create_research_agent() -> Agent:
    """
    Create a Research Agent that uses MCP tools for data gathering.

    The agent connects to the MCP server (mcp_server/server.py) via stdio
    transport. ADK's MCPToolset spawns the server as a subprocess and
    communicates via standard input/output.

    Returns:
        Configured ADK Agent instance with MCP tools.
    """
    # Resolve the absolute path to the MCP server script.
    # WHY: The MCP server is spawned as a subprocess, so we need the full
    # path regardless of what directory the CLI is run from.
    mcp_server_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "mcp_server",
        "server.py",
    )

    # Connect to the MCP server via stdio transport.
    # WHY: This creates a clean protocol boundary — the research tools
    # run in a separate process, discoverable through MCP, not imported
    # as Python functions.  sys.executable ensures the same Python
    # interpreter is used for the subprocess.
    mcp_tools = MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[mcp_server_path],
            )
        )
    )

    return Agent(
        name="research_agent",
        model=get_model_name(),
        description=(
            "Researches current trends, statistics, and competitor content "
            "using MCP-connected research tools."
        ),
        instruction="""You are a thorough content researcher.

YOUR TASK:
Research the topic chosen by the planner: {planned_topic}

Use ALL THREE available research tools:
1. search_trends — to find current trends related to the topic and niche
2. search_statistics — to find supporting data and numbers
3. search_competitor_content — to understand what others are posting

IMPORTANT:
- Call each tool and wait for its response.
- Compile all results into one structured research brief.
- If any tool call fails, note the failure and continue with the others.

OUTPUT FORMAT:

RESEARCH BRIEF FOR: [topic]

KEY TRENDS:
- [trend 1 with brief explanation]
- [trend 2 with brief explanation]
- [trend 3 with brief explanation]

SUPPORTING DATA:
- [statistic 1 with context]
- [statistic 2 with context]

COMPETITOR INSIGHTS:
- [what top voices are doing]
- [content gaps and opportunities]

RECOMMENDED ANGLE:
[Based on your research, suggest the best angle for the LinkedIn post]

DATA SOURCE NOTE:
[State whether results came from live search or mock fallback]

Be concise and factual. Focus on information that will make the LinkedIn post credible and engaging.""",
        tools=[mcp_tools],
        output_key="research_results",
    )
