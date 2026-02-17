"""Rich-based terminal reporter for agentrace.

Supports both legacy dict traces (Phase 1) and Trace model objects (Phase 2).
"""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree


def print_trace(trace: Any, detailed: bool = False, console: Console | None = None) -> None:
    """Print a trace report to the terminal using Rich.

    Args:
        trace: A TraceResult dict (legacy) or Trace model object.
        detailed: If True, show state diffs and timing table.
        console: Optional Rich Console (for testing / capture).
    """
    if console is None:
        console = Console()

    # Normalize: support both dict and Trace model
    if isinstance(trace, dict):
        _print_dict_trace(trace, detailed, console)
    else:
        _print_model_trace(trace, detailed, console)


def _print_dict_trace(trace: dict[str, Any], detailed: bool, console: Console) -> None:
    """Render a legacy dict trace."""
    nodes = trace["nodes"]
    total_ms = trace["total_duration_ms"]
    total_nodes = len(nodes)

    tree = Tree("[bold]agentrace[/bold]")
    for node in nodes:
        step = node["step"]
        name = node["node_name"]
        duration = node["duration_ms"]
        tree.add(f"[green]OK[/green] Step {step}: {name} ({duration:.1f}ms)")

    summary = f"[green]SUCCESS[/green] | {total_nodes} nodes | {total_ms:.1f}ms"
    panel = Panel(tree, title="[bold]agentrace[/bold]", subtitle=summary)
    console.print(panel)


def _print_model_trace(trace: Any, detailed: bool, console: Console) -> None:
    """Render a Trace model object."""
    from agentrace.core.models import NodeStatus

    nodes = trace.nodes
    meta = trace.metadata
    status_str = "[green]SUCCESS[/green]" if trace.successful else "[red]FAILED[/red]"

    tree = Tree("[bold]agentrace[/bold]")
    for node in nodes:
        if node.status == NodeStatus.SUCCESS:
            icon = "[green]OK[/green]"
        else:
            icon = "[red]ERR[/red]"
        label = f"{icon} Step {node.step}: {node.node_name} ({node.duration_ms:.1f}ms)"
        node_branch = tree.add(label)

        if detailed and node.state_diff:
            diff_str = json.dumps(node.state_diff, indent=2, default=str)
            node_branch.add(f"[dim]diff: {diff_str}[/dim]")

        if node.error:
            node_branch.add(f"[red]error: {node.error}[/red]")

    summary = f"{status_str} | {meta.total_nodes} nodes | {meta.duration_ms:.1f}ms"
    panel = Panel(tree, title="[bold]agentrace[/bold]", subtitle=summary)
    console.print(panel)

    if detailed:
        table = Table(title="Node Timing")
        table.add_column("Step", justify="right")
        table.add_column("Node")
        table.add_column("Duration (ms)", justify="right")
        table.add_column("Status")

        for node in nodes:
            status = "[green]OK[/green]" if node.status == NodeStatus.SUCCESS else "[red]ERR[/red]"
            table.add_row(
                str(node.step),
                node.node_name,
                f"{node.duration_ms:.1f}",
                status,
            )

        console.print(table)
