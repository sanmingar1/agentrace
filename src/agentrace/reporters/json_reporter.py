"""JSON reporter for agentrace traces.

Exports traces as JSON files for CI/CD pipelines and programmatic analysis.
"""

import json
from pathlib import Path
from typing import Any, Optional


def to_json(trace: Any, output_path: Optional[str] = None, indent: int = 2) -> str:
    """Export a trace as a JSON string.

    Args:
        trace: A Trace model or legacy dict trace.
        output_path: If provided, write JSON to this file path.
        indent: JSON indentation level.

    Returns:
        The JSON string.
    """
    if isinstance(trace, dict):
        json_str = json.dumps(trace, indent=indent, default=str)
    else:
        json_str = trace.model_dump_json(indent=indent)

    if output_path:
        Path(output_path).write_text(json_str, encoding="utf-8")

    return json_str
