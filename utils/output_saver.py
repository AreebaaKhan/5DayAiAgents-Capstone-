"""
Output saver utility — persists each agent's output as structured JSON.

WHY: Saving every agent's output to outputs/<run_id>/<agent>.json lets
judges inspect intermediate results, debug pipeline issues, and see
exactly what data flowed between agents.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def save_agent_output(
    agent_name: str,
    run_id: str,
    output_data: Any,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """
    Save an agent's output as structured JSON to the outputs/ directory.

    Args:
        agent_name: Name of the agent (e.g., "planner_agent").
        run_id: Unique identifier for this pipeline run.
        output_data: The agent's output — string, dict, or any JSON-serializable value.
        metadata: Optional additional context to include in the output record.

    Returns:
        Absolute path to the saved output file.
    """
    output_dir = Path("outputs") / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_record = {
        "agent": agent_name,
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "output": output_data,
        "metadata": metadata or {},
    }

    output_file = output_dir / f"{agent_name}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_record, f, indent=2, ensure_ascii=False)

    return str(output_file)
