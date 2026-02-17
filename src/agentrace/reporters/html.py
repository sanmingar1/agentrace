"""Self-contained HTML reporter for agentrace traces.

Generates a single HTML file with embedded Mermaid diagram,
expandable node details, state diffs, and summary statistics.
No external dependencies required to view the report.
"""

import json
from pathlib import Path
from typing import Any, Optional

from agentrace.reporters.mermaid import to_mermaid


def _get_trace_data(trace: Any) -> dict:
    """Extract trace data into a plain dict for the HTML template."""
    if isinstance(trace, dict):
        return {
            "nodes": [
                {
                    "name": n["node_name"],
                    "step": n.get("step", 0),
                    "status": n.get("status", "success"),
                    "duration_ms": n.get("duration_ms", 0),
                    "output": n.get("output", {}),
                    "state_diff": None,
                    "error": None,
                }
                for n in trace.get("nodes", [])
            ],
            "total_duration_ms": trace.get("total_duration_ms", 0),
            "node_count": len(trace.get("nodes", [])),
            "error_count": 0,
            "input": trace.get("input", {}),
            "output": trace.get("output", {}),
        }

    return {
        "nodes": [
            {
                "name": n.node_name,
                "step": n.step,
                "status": n.status.value,
                "duration_ms": n.duration_ms,
                "state_before": n.state_before,
                "state_after": n.state_after,
                "state_diff": n.state_diff,
                "error": n.error,
            }
            for n in trace.nodes
        ],
        "total_duration_ms": trace.metadata.duration_ms,
        "node_count": trace.metadata.total_nodes,
        "error_count": trace.metadata.error_count,
        "input": trace.metadata.input_data,
        "output": trace.metadata.output_data,
    }


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>agentrace Report</title>
<style>
  :root {{
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --text-dim: #8b949e; --accent: #58a6ff;
    --green: #3fb950; --red: #f85149; --yellow: #d29922;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); padding: 24px; line-height: 1.6; }}
  .container {{ max-width: 960px; margin: 0 auto; }}
  h1 {{ font-size: 24px; margin-bottom: 8px; }}
  .subtitle {{ color: var(--text-dim); margin-bottom: 24px; }}
  .stats {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .stat {{ background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px 20px; min-width: 140px; }}
  .stat-value {{ font-size: 28px; font-weight: 700; }}
  .stat-label {{ color: var(--text-dim); font-size: 13px; }}
  .stat-value.success {{ color: var(--green); }}
  .stat-value.error {{ color: var(--red); }}
  .mermaid-section {{ background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 20px; margin-bottom: 24px; }}
  .mermaid-section h2 {{ margin-bottom: 12px; font-size: 16px; }}
  .mermaid {{ background: #fff; border-radius: 6px; padding: 16px; text-align: center; }}
  .nodes-section h2 {{ font-size: 16px; margin-bottom: 12px; }}
  .node-card {{ background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; margin-bottom: 8px; overflow: hidden; }}
  .node-header {{ display: flex; align-items: center; padding: 12px 16px;
    cursor: pointer; gap: 10px; user-select: none; }}
  .node-header:hover {{ background: rgba(255,255,255,0.03); }}
  .node-icon {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
  .node-icon.success {{ background: var(--green); }}
  .node-icon.error {{ background: var(--red); }}
  .node-name {{ font-weight: 600; flex: 1; }}
  .node-step {{ color: var(--text-dim); font-size: 13px; }}
  .node-duration {{ color: var(--text-dim); font-size: 13px; }}
  .node-chevron {{ color: var(--text-dim); transition: transform 0.2s; }}
  .node-card.open .node-chevron {{ transform: rotate(90deg); }}
  .node-body {{ display: none; padding: 0 16px 16px; border-top: 1px solid var(--border); }}
  .node-card.open .node-body {{ display: block; padding-top: 12px; }}
  .detail-label {{ color: var(--text-dim); font-size: 12px; text-transform: uppercase;
    letter-spacing: 0.5px; margin-bottom: 4px; margin-top: 12px; }}
  .detail-label:first-child {{ margin-top: 0; }}
  pre {{ background: var(--bg); border: 1px solid var(--border); border-radius: 6px;
    padding: 12px; font-size: 13px; overflow-x: auto;
    white-space: pre-wrap; word-break: break-word; }}
  .error-text {{ color: var(--red); }}
  .footer {{ text-align: center; color: var(--text-dim); font-size: 12px;
    margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="container">
  <h1>agentrace Report</h1>
  <p class="subtitle">{status_text}</p>

  <div class="stats">
    <div class="stat">
      <div class="stat-value {status_class}">{status_label}</div>
      <div class="stat-label">Status</div>
    </div>
    <div class="stat">
      <div class="stat-value">{node_count}</div>
      <div class="stat-label">Nodes Visited</div>
    </div>
    <div class="stat">
      <div class="stat-value">{total_duration}</div>
      <div class="stat-label">Total Duration</div>
    </div>
    <div class="stat">
      <div class="stat-value {error_class}">{error_count}</div>
      <div class="stat-label">Errors</div>
    </div>
  </div>

  <div class="mermaid-section">
    <h2>Execution Flow</h2>
    <div class="mermaid">
{mermaid_code}
    </div>
  </div>

  <div class="nodes-section">
    <h2>Node Details</h2>
{node_cards}
  </div>

  <div class="footer">Generated by agentrace</div>
</div>

<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
document.querySelectorAll('.node-header').forEach(h => {{
  h.addEventListener('click', () => h.parentElement.classList.toggle('open'));
}});
</script>
</body>
</html>
"""


def _build_node_card(node: dict) -> str:
    """Build HTML for a single node card."""
    status = node["status"]
    icon_class = "success" if status == "success" else "error"
    duration = f"{node['duration_ms']:.1f}ms"

    body_parts = []

    if node.get("error"):
        body_parts.append(
            f'    <div class="detail-label">Error</div>\n'
            f'    <pre class="error-text">{_escape(node["error"])}</pre>'
        )

    if node.get("state_diff"):
        body_parts.append(
            f'    <div class="detail-label">State Diff</div>\n'
            f"    <pre>{_escape(json.dumps(node['state_diff'], indent=2, default=str))}</pre>"
        )

    if node.get("state_before"):
        body_parts.append(
            f'    <div class="detail-label">State Before</div>\n'
            f"    <pre>{_escape(json.dumps(node['state_before'], indent=2, default=str))}</pre>"
        )

    if node.get("state_after"):
        body_parts.append(
            f'    <div class="detail-label">State After</div>\n'
            f"    <pre>{_escape(json.dumps(node['state_after'], indent=2, default=str))}</pre>"
        )

    # For dict traces that have "output" instead of state_before/after
    if node.get("output") and not node.get("state_after"):
        body_parts.append(
            f'    <div class="detail-label">Output</div>\n'
            f"    <pre>{_escape(json.dumps(node['output'], indent=2, default=str))}</pre>"
        )

    body_html = "\n".join(body_parts) if body_parts else "    <p>No details available</p>"

    return f"""\
    <div class="node-card">
      <div class="node-header">
        <span class="node-icon {icon_class}"></span>
        <span class="node-name">{_escape(node["name"])}</span>
        <span class="node-step">Step {node["step"]}</span>
        <span class="node-duration">{duration}</span>
        <span class="node-chevron">&#9654;</span>
      </div>
      <div class="node-body">
{body_html}
      </div>
    </div>"""


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def to_html(trace: Any, output_path: Optional[str] = None) -> str:
    """Generate a self-contained HTML report from a trace.

    Args:
        trace: A Trace model or legacy dict trace.
        output_path: If provided, write the HTML to this file path.

    Returns:
        The HTML string.
    """
    data = _get_trace_data(trace)
    mermaid_code = to_mermaid(trace)

    has_errors = data["error_count"] > 0
    status_label = "FAILED" if has_errors else "SUCCESS"
    status_class = "error" if has_errors else "success"
    status_text = f"{data['node_count']} nodes executed in {data['total_duration_ms']:.1f}ms"
    error_class = "error" if has_errors else "success"

    node_cards = "\n".join(_build_node_card(n) for n in data["nodes"])

    html = _HTML_TEMPLATE.format(
        status_text=status_text,
        status_label=status_label,
        status_class=status_class,
        node_count=data["node_count"],
        total_duration=f"{data['total_duration_ms']:.1f}ms",
        error_count=data["error_count"],
        error_class=error_class,
        mermaid_code=mermaid_code,
        node_cards=node_cards,
    )

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")

    return html
