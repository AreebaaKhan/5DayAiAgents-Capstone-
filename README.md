# 🤖 AI Brand Content Strategist

> **A multi-agent AI system that autonomously plans, researches, writes, illustrates, and publishes LinkedIn content.**

Built for the **Google + Kaggle 5-Day AI Agents Capstone** hackathon, this project demonstrates modern AI agent concepts: multi-agent orchestration, tool use via MCP, human-in-the-loop oversight, graceful fallback design, and now a browser UI on top of the existing CLI pipeline.

---

## 📌 Problem Statement

Creating consistent, high-quality LinkedIn content is time-consuming. A professional must:

1. **Decide** what to post about (topic selection)
2. **Research** current trends and data (credibility)
3. **Write** an engaging post (copywriting)
4. **Create** a supporting visual (engagement)
5. **Review** before publishing (quality control)

Each step requires different expertise. Instead of a single monolithic LLM call, this project uses **specialized AI agents** — each focused on one responsibility — orchestrated into a reliable pipeline.

---

## 🧠 Why Multi-Agent Instead of One LLM Call?

| Single LLM Call | Multi-Agent System |
|---|---|
| One prompt does everything → inconsistent quality | Each agent is an expert at one task |
| No separation of concerns | Clean boundaries (MCP, tools, session state) |
| Hard to debug or improve individual steps | Each agent can be tested and improved independently |
| No natural point for human review | Human approval gate between generation and publishing |
| All-or-nothing failure | Graceful fallbacks at each stage |

---

## 🏗️ Architecture

```
                    ┌──────────────────────────┐
                    │   CLI (cli.py) /          │
                    │   Streamlit UI            │
                    │   Persona Selection &     │
                    │   Pipeline Launcher       │
                    └───────────┬──────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│            SequentialAgent Pipeline (pipeline.py)              │
│                                                               │
│  ┌──────────────┐   ┌────────────────┐   ┌────────────────┐  │
│  │ 1. PLANNER   │──▶│ 2. RESEARCHER  │──▶│ 3. WRITER      │  │
│  │    Agent      │   │    Agent        │   │    Agent        │  │
│  │              │   │                │   │                │  │
│  │ Picks topic  │   │  Uses MCP      │   │ Writes post    │  │
│  │ + reasoning  │   │  protocol      │   │ Hook/Body/CTA  │  │
│  └──────────────┘   └───────┬────────┘   └────────────────┘  │
│                             │ stdio                           │
│                     ┌───────▼────────┐                        │
│                     │   MCP Server   │                        │
│                     │   (FastMCP)    │                        │
│                     │               │                        │
│                     │ search_trends  │                        │
│                     │ search_stats   │                        │
│                     │ search_comp.   │                        │
│                     └────────────────┘                        │
│                                                               │
│  ┌──────────────┐   ┌─────────────────────────────────────┐  │
│  │ 4. VISUAL    │──▶│ 5. PUBLISHER Agent                   │  │
│  │    Agent      │   │                                     │  │
│  │              │   │  ┌─────────────────────────────┐    │  │
│  │ Pillow       │   │  │ HUMAN APPROVAL GATE         │    │  │
│  │ infographic  │   │  │ (blocks for user input)     │    │  │
│  │              │   │  └──────────────┬──────────────┘    │  │
│  └──────────────┘   │                │                     │  │
│                     │    Approved? ──▶ Publish / Simulate   │  │
│                     └─────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent Responsibilities

| Agent | Role | Input | Output | Key Feature |
|---|---|---|---|---|
| **Planner** | Choose today's topic | Persona profile + current date | Topic + reasoning | Date-aware decisions |
| **Researcher** | Gather supporting data | Topic from Planner | Trends, stats, competitor insights | **MCP protocol boundary** |
| **Writer** | Write LinkedIn post | Topic + Research | Hook, Body, CTA, Hashtags | Persona tone matching |
| **Visual** | Create infographic | Post content | PNG image (1200×627) | **Pillow** — always works locally |
| **Publisher** | Approve & publish | Post + Image | Publish record | **Human-in-the-loop gate** |

---

## 🔌 MCP (Model Context Protocol) Explained

The Research Agent does **NOT** import Python functions directly. Instead, it communicates with research tools through the **Model Context Protocol**:

```
Research Agent  ──── stdio transport ────▶  MCP Server (mcp_server/server.py)
                                                    │
                                                    ├── search_trends()
                                                    ├── search_statistics()
                                                    └── search_competitor_content()
```

**Why MCP matters:**
- **Clean boundary**: Tools are in a separate process, discoverable via protocol
- **Swappable**: You can replace the MCP server without changing the agent
- **Standardized**: MCP is an industry-standard protocol for AI tool integration
- **Observable**: Tool calls are logged and auditable

**Transport**: stdio (standard input/output) — the MCP server runs as a subprocess.

---

## 👤 Human Oversight

The Publisher Agent implements a **genuine human-in-the-loop gate**:

1. The full post and image path are displayed to the user
2. The pipeline **blocks** waiting for user input (`yes` / `no` / `edit`)
3. Only if the user explicitly approves does publishing proceed
4. Rejection feedback is recorded and reported

This is **not simulated approval** — the system truly waits for human action.

---

## 📁 Project Structure

```
Project/
├── cli.py                  # Main entry point — interactive CLI
├── streamlit_app.py        # Browser UI for running the pipeline
├── pipeline.py             # SequentialAgent orchestrator
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
│
├── agents/                 # All 5 specialized agents
│   ├── __init__.py
│   ├── planner_agent.py    # Topic selection + reasoning
│   ├── research_agent.py   # MCP-connected research
│   ├── writer_agent.py     # LinkedIn post generation
│   ├── visual_agent.py     # Pillow infographic creation
│   └── publisher_agent.py  # Human approval + publishing
│
├── mcp_server/             # MCP research tool server
│   ├── server.py           # FastMCP server (stdio transport)
│   └── tools.py            # Search tools (real + mock fallback)
│
├── personas/               # Brand persona configurations
│   ├── python_mentor.json
│   ├── startup_founder.json
│   └── restaurant_owner.json
│
├── utils/                  # Shared utilities
│   ├── __init__.py
│   ├── logger.py           # Structured JSON + console logging
│   └── output_saver.py     # Agent output persistence
│
├── logs/                   # Pipeline execution logs (auto-created)
├── outputs/                # Agent outputs as JSON (auto-created)
├── assets/
│   └── generated/          # Generated infographics (auto-created)
│
└── README.md               # This file
```

---

## 🚀 Setup

### Prerequisites

- **Python 3.11+**
- **Google API Key** — [Get one here](https://aistudio.google.com/apikey)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Project

# 2. Create a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux

# 5. Edit .env and add your Google API key
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | ✅ Yes | Your Gemini API key |
| `GOOGLE_GENAI_USE_VERTEXAI` | ✅ Yes | Set to `FALSE` (uses API key auth) |
| `SERPER_API_KEY` | ❌ Optional | [Serper.dev](https://serper.dev) key for real web search |
| `LINKEDIN_ACCESS_TOKEN` | ❌ Optional | LinkedIn API token for real publishing |

---

## ⚙️ Configuration

### Adding a New Persona

Create a new JSON file in `personas/`:

```json
{
    "name": "Data Scientist",
    "niche": "Machine Learning & Data Science",
    "tone": "Analytical, curious, and approachable",
    "audience": "Data professionals, ML engineers, analytics managers",
    "posting_goal": "Share practical ML insights and build community",
    "posting_frequency": "3 times per week",
    "example_topics": [
        "Feature engineering tips",
        "MLOps best practices",
        "Data visualization techniques"
    ]
}
```

The CLI will automatically discover any `.json` file in the `personas/` directory.

---

## ▶️ How to Run

```bash
# Make sure your virtual environment is activated and .env is configured

python cli.py
```

The CLI will:
1. Check your API key configuration
2. List available personas
3. Let you select one
4. Run the full 5-agent pipeline
5. Pause for your approval before publishing
6. Display results and save outputs

### Browser UI

```bash
streamlit run streamlit_app.py
```

The browser UI lets you select a persona, launch the pipeline, and review the generated post, research brief, image, and publish record in tabs. Because the original approval step is CLI-based, the Streamlit app uses automatic approval so the run can complete in the browser. Use the CLI if you want to manually type approve/reject responses.

### Expected Output

```
╔═══════════════════════════════════════════════════════════════╗
║   🤖  AI Brand Content Strategist                             ║
║   Multi-Agent LinkedIn Content Pipeline                       ║
╚═══════════════════════════════════════════════════════════════╝

✓ Google API key configured
○ No Serper API key — using mock search (fallback)
○ No LinkedIn token — publishing will be simulated

Available Personas:
──────────────────────────────────────────────────────
  1. Python Mentor
     Niche:    Python Programming & Software Engineering
     Tone:     Educational, encouraging, technically precise

  2. Startup Founder
     ...

Select a persona (1-3): 1

──────────────────────────────────────────────────────
▶ planner_agent starting...
✓ planner_agent completed (3.2s) [success]
──────────────────────────────────────────────────────
▶ research_agent starting...
✓ research_agent completed (5.1s) [success]
  ⚠ Fallback was used
──────────────────────────────────────────────────────
▶ writer_agent starting...
✓ writer_agent completed (4.0s) [success]
──────────────────────────────────────────────────────
▶ visual_agent starting...
✓ visual_agent completed (1.2s) [success]
──────────────────────────────────────────────────────
▶ publisher_agent starting...

🔔  HUMAN APPROVAL REQUIRED
════════════════════════════════════════════════════════
📝 LINKEDIN POST FOR REVIEW:
────────────────────────────────────
[The generated LinkedIn post appears here]
────────────────────────────────────
🖼️  Generated Image: assets/generated/infographic_20260705_010000.png

✅ Approve this post? (yes / no / edit): yes

📤  SIMULATED PUBLISH
════════════════════════════════════════════════════════
⚠️  This is a SIMULATION — no real LinkedIn post was created.
📄 Publish record saved: assets/generated/publish_record_20260705_010000.json

✨ Pipeline complete!
```

---

## 📤 Real vs. Simulated Publishing

| Scenario | Behavior |
|---|---|
| `LINKEDIN_ACCESS_TOKEN` is set | Attempts real LinkedIn API publish |
| API call succeeds | Reports `REAL_PUBLISH_SUCCESS` |
| API call fails | Falls back to simulated publish + logs error |
| No token configured | **SIMULATED PUBLISH** (clearly labeled) |

Simulated publishes save a JSON record to `assets/generated/` for verification. The output **never** pretends simulation is a real publish.

---

## 📚 Course Concepts Demonstrated

### Multi-Agent Systems (ADK)
- **SequentialAgent** for deterministic pipeline orchestration
- **5 specialized agents**, each with focused responsibilities
- **Session state sharing** via `output_key` for inter-agent communication
- **Agent tools** (function tools) for grounding agents in real capabilities

### Model Context Protocol (MCP)
- **FastMCP server** with stdio transport
- **MCPToolset** integration in ADK for tool discovery
- **Protocol boundary**: Research tools are in a separate process
- **Real + mock search** with graceful fallback

### Human Oversight
- **Genuine human-in-the-loop** approval gate (not simulated)
- Pipeline **blocks** on user input before publishing
- Supports approve, reject, and edit-request flows

### Security
- All secrets in `.env` (never hardcoded)
- `.env` excluded from git via `.gitignore`
- `.env.example` provided for easy setup

### Deployability
- Clean `requirements.txt` with standard packages
- No hardcoded paths — works on Windows, macOS, and Linux
- Structured logging for production observability
- JSON outputs for downstream integration

---

## ⚠️ Limitations

- **Search is mocked by default**: Without a `SERPER_API_KEY`, research tools return realistic but static mock data
- **Image generation is basic**: Uses Pillow templates rather than AI image generation
- **LinkedIn publishing**: Requires a valid OAuth token (complex to obtain for demos)
- **No conversation memory**: Each pipeline run is independent (InMemorySessionService)
- **Single pipeline run**: No batch processing or scheduling
- **No content revision loop**: If the user rejects the post, the pipeline ends

---

## 🔮 Future Improvements

- **Real search integration**: SerpAPI, Google Custom Search, or Tavily for live data
- **AI image generation**: Gemini Imagen or DALL-E for dynamic visuals
- **Content revision loop**: `LoopAgent` to revise content based on human feedback
- **Multi-platform support**: Twitter/X, Instagram, newsletter generation
- **Content calendar**: Plan and schedule a week of content at once
- **Analytics feedback**: Use post performance data to improve future content
- **Persistent memory**: Store past topics to avoid repetition
- **A/B testing**: Generate multiple post variants and let the user choose

---

## 📄 License

Built for the Google + Kaggle 5-Day AI Agents Capstone hackathon.
