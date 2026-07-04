"""
CLI Entry Point — Interactive command-line interface for the AI Brand Content Strategist.

WHY: This is the main user-facing interface. It provides a clean, guided
experience for selecting a persona and running the content strategy pipeline.
Preferred over Streamlit for simplicity and hackathon reliability.

Usage:
    python cli.py

The CLI will:
1. Check that the Google API key is configured
2. List available personas from the personas/ directory
3. Let the user select a persona
4. Run the full 5-agent pipeline
5. Display formatted results
"""

import asyncio
import json
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode symbols
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

# Load environment variables BEFORE importing anything that needs them
load_dotenv()

import os

from utils.logger import Colors


# ── Banner ────────────────────────────────────────────────────────────

def display_banner() -> None:
    """Display a professional ASCII banner for the tool."""
    print(f"""
{Colors.BLUE}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🤖  AI Brand Content Strategist                             ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                              ║
║   Multi-Agent LinkedIn Content Pipeline                       ║
║                                                               ║
║   Powered by Google ADK  •  Gemini  •  MCP                    ║
║   Google + Kaggle 5-Day AI Agents Capstone                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.ENDC}""")


# ── Prerequisites check ──────────────────────────────────────────────

def check_api_key() -> bool:
    """
    Verify that the Google API key is configured and report
    the status of optional integrations (search, LinkedIn).

    Returns:
        True if the required API key is present, False otherwise.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key or api_key == "your-google-api-key-here":
        print(f"\n{Colors.FAIL}✗ ERROR: GOOGLE_API_KEY not found or not set.{Colors.ENDC}")
        print(f"{Colors.WARNING}  1. Copy .env.example to .env{Colors.ENDC}")
        print(f"{Colors.WARNING}  2. Add your Google API key from https://aistudio.google.com/apikey{Colors.ENDC}")
        return False

    print(f"{Colors.GREEN}✓ Google API key configured{Colors.ENDC}")

    # Report optional integration status
    if os.environ.get("SERPER_API_KEY"):
        print(f"{Colors.GREEN}✓ Serper API key found — real web search enabled{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}○ No Serper API key — using mock search (fallback){Colors.ENDC}")

    if os.environ.get("LINKEDIN_ACCESS_TOKEN"):
        print(f"{Colors.GREEN}✓ LinkedIn token found — real publishing enabled{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}○ No LinkedIn token — publishing will be simulated{Colors.ENDC}")

    return True


# ── Persona loading ──────────────────────────────────────────────────

def load_personas() -> list[dict]:
    """
    Load all persona configurations from the personas/ directory.

    Returns:
        List of dicts, each with 'file', 'path', and 'data' keys.
        Empty list if the directory is missing or contains no valid JSON.
    """
    personas_dir = Path("personas")
    if not personas_dir.exists():
        print(f"{Colors.FAIL}✗ ERROR: personas/ directory not found.{Colors.ENDC}")
        return []

    personas = []
    for filepath in sorted(personas_dir.glob("*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                personas.append({
                    "file": filepath.name,
                    "path": str(filepath),
                    "data": data,
                })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"{Colors.WARNING}⚠ Skipping {filepath.name}: {e}{Colors.ENDC}")

    return personas


# ── Interactive persona selection ─────────────────────────────────────

def select_persona(personas: list[dict]) -> dict:
    """
    Let the user select a persona interactively from the available options.

    Args:
        personas: List of loaded persona records.

    Returns:
        The selected persona's data dict.
    """
    print(f"\n{Colors.BOLD}Available Personas:{Colors.ENDC}")
    print(f"{'─' * 50}")

    for i, p in enumerate(personas, 1):
        data = p["data"]
        print(f"  {Colors.CYAN}{i}.{Colors.ENDC} {Colors.BOLD}{data['name']}{Colors.ENDC}")
        print(f"     Niche:    {data['niche']}")
        print(f"     Tone:     {data['tone']}")
        print(f"     Audience: {data['audience']}")
        print()

    while True:
        try:
            choice = input(
                f"{Colors.BOLD}Select a persona (1-{len(personas)}): {Colors.ENDC}"
            ).strip()
            index = int(choice) - 1
            if 0 <= index < len(personas):
                selected = personas[index]
                print(f"\n{Colors.GREEN}✓ Selected: {selected['data']['name']}{Colors.ENDC}")
                return selected["data"]
            print(f"{Colors.WARNING}  Please enter a number between 1 and {len(personas)}.{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.WARNING}  Please enter a valid number.{Colors.ENDC}")


# ── Results display ──────────────────────────────────────────────────

def display_results(results: dict) -> None:
    """
    Display the pipeline results in a formatted, readable layout.

    Args:
        results: The dict returned by run_pipeline().
    """
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'═' * 60}{Colors.ENDC}")
    print(f"{Colors.BLUE}{Colors.BOLD}📊 Pipeline Results{Colors.ENDC}")
    print(f"{Colors.BLUE}{'═' * 60}{Colors.ENDC}")

    agent_results = results.get("results", {})

    # Planned topic
    print(f"\n{Colors.BOLD}📋 Planned Topic:{Colors.ENDC}")
    topic = agent_results.get("planner_agent", "N/A")
    # Show first 300 chars to keep display manageable
    print(f"   {str(topic)[:300]}")

    # Research summary
    print(f"\n{Colors.BOLD}🔍 Research Summary:{Colors.ENDC}")
    research = agent_results.get("research_agent", "N/A")
    print(f"   {str(research)[:400]}...")

    # The LinkedIn post — show in full
    print(f"\n{Colors.BOLD}📝 LinkedIn Post:{Colors.ENDC}")
    print(f"{'─' * 50}")
    print(agent_results.get("writer_agent", "N/A"))
    print(f"{'─' * 50}")

    # Image path
    print(f"\n{Colors.BOLD}🖼️  Generated Visual:{Colors.ENDC}")
    print(f"   {agent_results.get('visual_agent', 'N/A')}")

    # Publish result
    print(f"\n{Colors.BOLD}📤 Publish Result:{Colors.ENDC}")
    print(f"   {str(agent_results.get('publisher_agent', 'N/A'))[:300]}")

    # Output file locations
    run_id = results.get("run_id", "unknown")
    print(f"\n{Colors.BOLD}📁 Output Files:{Colors.ENDC}")
    print(f"   Logs:    logs/run_{run_id}.json")
    print(f"   Outputs: outputs/{run_id}/")
    print(f"   Images:  assets/generated/")

    print(f"\n{Colors.GREEN}{Colors.BOLD}✨ Pipeline complete!{Colors.ENDC}\n")


# ── Main entry point ─────────────────────────────────────────────────

async def main() -> None:
    """Main CLI entry point — guides the user through the full pipeline."""
    display_banner()

    # 1. Check prerequisites
    if not check_api_key():
        sys.exit(1)

    # 2. Load personas
    personas = load_personas()
    if not personas:
        print(f"{Colors.FAIL}✗ No personas found. Check the personas/ directory.{Colors.ENDC}")
        sys.exit(1)

    # 3. Select persona
    persona = select_persona(personas)

    # 4. Confirm before running (the pipeline makes API calls)
    print(f"\n{Colors.BOLD}Ready to run the content pipeline for '{persona['name']}'.{Colors.ENDC}")
    confirm = input("Continue? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y", ""):
        print("Cancelled.")
        sys.exit(0)

    # 5. Run the pipeline
    try:
        from pipeline import run_pipeline

        results = await run_pipeline(persona)
        display_results(results)

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Pipeline interrupted by user.{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.FAIL}{'─' * 60}{Colors.ENDC}")
        print(f"{Colors.FAIL}✗ Pipeline error: {e}{Colors.ENDC}")
        print(f"{Colors.FAIL}{'─' * 60}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
