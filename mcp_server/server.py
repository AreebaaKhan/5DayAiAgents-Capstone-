"""
MCP Server — exposes research tools over the Model Context Protocol.

WHY: This is the MCP BOUNDARY. The Research Agent discovers and calls these
tools through the MCP protocol (stdio transport), NOT through direct Python
imports. This demonstrates a clean architectural separation where tools can
be versioned, swapped, or deployed independently from the agents.

TRANSPORT: stdio (standard input/output)
FRAMEWORK: FastMCP
TOOLS EXPOSED: search_trends, search_statistics, search_competitor_content

To run manually:   python mcp_server/server.py
In the pipeline:   ADK's MCPToolset spawns this as a subprocess automatically.
"""

import sys
import os

# ── Path setup ────────────────────────────────────────────────────────
# WHY: When ADK spawns this script as a subprocess, the working directory
# is the project root, not mcp_server/. We add this script's directory to
# sys.path so that `from tools import ...` resolves correctly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Load environment variables ────────────────────────────────────────
# WHY: The research tools check for SERPER_API_KEY to decide whether to
# use real search or mock fallback. The .env file lives in the project root.
from dotenv import load_dotenv

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_project_root, ".env"))

# ── FastMCP server setup ──────────────────────────────────────────────
from fastmcp import FastMCP
from tools import search_trends, search_statistics, search_competitor_content

# Initialize the MCP server with a descriptive name
mcp = FastMCP(
    "BrandResearchServer",
    instructions=(
        "Research tools for brand content strategy. "
        "Provides trend analysis, statistics, and competitor content insights."
    ),
)

# Register each research tool with the MCP server.
# WHY: We use the decorator-call pattern rather than @mcp.tool because
# the functions are defined in a separate module (tools.py).
search_trends = mcp.tool(search_trends)
search_statistics = mcp.tool(search_statistics)
search_competitor_content = mcp.tool(search_competitor_content)


if __name__ == "__main__":
    # Run the MCP server using stdio transport.
    # ADK's MCPToolset will spawn this process and communicate via stdin/stdout.
    mcp.run(transport="stdio")
