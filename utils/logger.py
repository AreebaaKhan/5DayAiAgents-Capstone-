"""
Structured logging utility for the AI Brand Content Strategist.

WHY: Every agent execution needs to be logged for debugging and demo purposes.
Logs are written as structured JSON for machine readability, and also printed
to console with colors for human readability during demos.

EXTENSIONS (per user request):
- Execution time tracking per agent
- Fallback usage tracking (e.g., mock search vs real search)
- Error recording with context
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ── Fix Windows console encoding ─────────────────────────────────────
# WHY: Windows cmd/PowerShell defaults to cp1252 which can't render Unicode
# symbols (─, ═, ▶, ✓, ✗). Reconfigure stdout to UTF-8 so colored
# console output works correctly on all platforms.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ── ANSI color codes for terminal output ──────────────────────────────
# WHY: Colored console output makes demos visually engaging and helps
# judges quickly see pipeline progress at a glance.
class Colors:
    """Terminal color codes for pretty console output during demos."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


class AgentLogger:
    """
    Structured logger that writes JSON logs to files and colored output to console.

    Each pipeline run gets its own log file in the logs/ directory, keyed by run_id.
    Tracks execution time, fallback usage, and errors for every agent.
    """

    def __init__(self, run_id: str) -> None:
        """
        Initialize logger for a specific pipeline run.

        Args:
            run_id: Unique identifier for this pipeline execution.
        """
        self.run_id = run_id
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"run_{run_id}.json"
        self.entries: list[dict[str, Any]] = []
        self._timers: dict[str, float] = {}

    # ── Agent lifecycle logging ───────────────────────────────────────

    def log_agent_start(self, agent_name: str, input_summary: str) -> None:
        """Record that an agent has begun execution and start its timer."""
        self._timers[agent_name] = time.time()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "agent": agent_name,
            "event": "start",
            "input_summary": input_summary[:500],
        }
        self.entries.append(entry)
        self._write_log()

        # Console output for demo visibility
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'─' * 60}{Colors.ENDC}")
        print(f"{Colors.CYAN}▶ {agent_name} starting...{Colors.ENDC}")
        print(f"{Colors.DIM}  Input: {input_summary[:120]}...{Colors.ENDC}")

    def log_agent_end(
        self,
        agent_name: str,
        output_summary: str,
        status: str = "success",
        fallback_used: bool = False,
        error: Optional[str] = None,
    ) -> None:
        """
        Record that an agent has completed execution.

        Args:
            agent_name: Which agent finished.
            output_summary: Brief description of what was produced.
            status: 'success' or 'error'.
            fallback_used: True if a fallback path was taken (e.g., mock search).
            error: Error message if status is 'error'.
        """
        elapsed = time.time() - self._timers.get(agent_name, time.time())
        entry = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "agent": agent_name,
            "event": "end",
            "status": status,
            "execution_time_seconds": round(elapsed, 2),
            "output_summary": output_summary[:500],
            "fallback_used": fallback_used,
            "error": error,
        }
        self.entries.append(entry)
        self._write_log()

        # Console output
        status_color = Colors.GREEN if status == "success" else Colors.FAIL
        print(f"{status_color}✓ {agent_name} completed ({elapsed:.1f}s) [{status}]{Colors.ENDC}")
        if fallback_used:
            print(f"{Colors.WARNING}  ⚠ Fallback was used{Colors.ENDC}")
        if error:
            print(f"{Colors.FAIL}  ✗ Error: {error}{Colors.ENDC}")

    def log_error(self, agent_name: str, error: str) -> None:
        """Record an error that occurred during agent execution."""
        elapsed = time.time() - self._timers.get(agent_name, time.time())
        entry = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "agent": agent_name,
            "event": "error",
            "status": "error",
            "execution_time_seconds": round(elapsed, 2),
            "error": str(error),
        }
        self.entries.append(entry)
        self._write_log()
        print(f"{Colors.FAIL}✗ {agent_name} error: {error}{Colors.ENDC}")

    # ── Pipeline summary ──────────────────────────────────────────────

    def log_pipeline_summary(self) -> None:
        """Print a formatted summary of the entire pipeline run to console."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'═' * 60}{Colors.ENDC}")
        print(f"{Colors.HEADER}📊 Pipeline Run Summary: {self.run_id}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'═' * 60}{Colors.ENDC}")

        for entry in self.entries:
            if entry["event"] == "end":
                status_icon = "✓" if entry["status"] == "success" else "✗"
                fallback = " [FALLBACK]" if entry.get("fallback_used") else ""
                err = f" — {entry['error']}" if entry.get("error") else ""
                print(
                    f"  {status_icon} {entry['agent']}: "
                    f"{entry['execution_time_seconds']}s{fallback}{err}"
                )

        total_time = sum(
            e["execution_time_seconds"]
            for e in self.entries
            if e["event"] == "end"
        )
        print(f"\n  Total execution time: {total_time:.1f}s")
        print(f"  Log file: {self.log_file}")
        print(f"{Colors.HEADER}{'═' * 60}{Colors.ENDC}\n")

    # ── Internal helpers ──────────────────────────────────────────────

    def _write_log(self) -> None:
        """Persist all log entries to the JSON log file."""
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2, ensure_ascii=False)
