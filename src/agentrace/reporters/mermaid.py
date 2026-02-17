"""Mermaid diagram generator for agentrace traces.

Generates Mermaid graph syntax from Trace objects for visualization
in GitHub READMEs, documentation, and HTML reports.
"""

from typing import Any


def _get_node_info(trace: Any) -> list[dict]:
    """Extract node info as list of dicts with name, status, duration_ms."""
    if isinstance(trace, dict):
        return [
            {
                "name": n["node_name"],
                "status": n.get("status", "success"),
                "duration_ms": n.get("duration_ms", 0),
            }
            for n in trace.get("nodes", [])
        ]
    return [
        {
            "name": n.node_name,
            "status": n.status.value,
            "duration_ms": n.duration_ms,
        }
        for n in trace.nodes
    ]


def _get_edge_info(trace: Any) -> list[dict]:
    """Extract edge info as list of dicts with from_node, to_node."""
    if isinstance(trace, dict):
        return [{"from_node": e[0], "to_node": e[1]} for e in trace.get("edges", [])]
    return [{"from_node": e.from_node, "to_node": e.to_node} for e in trace.edges]


def _sanitize_id(name: str) -> str:
    """Make a node name safe for Mermaid IDs."""
    return name.replace(" ", "_").replace("-", "_")


_STATUS_STYLES = {
    "success": "fill:#d4edda,stroke:#28a745,color:#155724",
    "error": "fill:#f8d7da,stroke:#dc3545,color:#721c24",
}


def to_mermaid(trace: Any, direction: str = "TD") -> str:
    """Generate a Mermaid flowchart from a trace.

    Args:
        trace: A Trace model or legacy dict trace.
        direction: Graph direction - "TD" (top-down) or "LR" (left-right).

    Returns:
        Mermaid flowchart string.
    """
    nodes = _get_node_info(trace)
    edges = _get_edge_info(trace)
    lines = [f"graph {direction}"]

    # Start node
    if nodes:
        first_id = _sanitize_id(nodes[0]["name"])
        lines.append(f"    START(( )) --> {first_id}")

    # Node definitions with duration labels
    for node in nodes:
        nid = _sanitize_id(node["name"])
        duration = node["duration_ms"]
        label = f"{node['name']}\\n{duration:.1f}ms"
        lines.append(f'    {nid}["{label}"]')

    # Last node to END
    if nodes:
        last_id = _sanitize_id(nodes[-1]["name"])
        lines.append(f"    {last_id} --> END(( ))")

    # Edges
    for edge in edges:
        from_id = _sanitize_id(edge["from_node"])
        to_id = _sanitize_id(edge["to_node"])
        lines.append(f"    {from_id} --> {to_id}")

    # Styles by status
    for node in nodes:
        nid = _sanitize_id(node["name"])
        style = _STATUS_STYLES.get(node["status"], _STATUS_STYLES["success"])
        lines.append(f"    style {nid} {style}")

    # Style start/end circles
    lines.append("    style START fill:#000,stroke:#000,color:#fff")
    lines.append("    style END fill:#000,stroke:#000,color:#fff")

    return "\n".join(lines)
