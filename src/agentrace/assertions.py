"""Assertion functions for agentrace.

Provides pytest-compatible assertions for validating agent behavior.
Supports both legacy dict traces and Trace model objects.
"""

from typing import Any, Optional


def _get_node_names(trace: Any) -> list[str]:
    """Extract node names from either a dict trace or Trace model."""
    if isinstance(trace, dict):
        return trace["node_names"]
    return trace.node_names


def _get_edges(trace: Any) -> list[tuple[str, str]]:
    """Extract edge tuples (from, to) from either a dict trace or Trace model."""
    if isinstance(trace, dict):
        return trace.get("edges", [])
    return [(e.from_node, e.to_node) for e in trace.edges]


def _get_nodes(trace: Any) -> list[Any]:
    """Extract node execution objects/dicts from trace."""
    if isinstance(trace, dict):
        return trace.get("nodes", [])
    return trace.nodes


def _get_node_status(node: Any) -> str:
    """Get status string from a node execution (dict or model)."""
    if isinstance(node, dict):
        return node.get("status", "success")
    return node.status.value


def _get_node_name(node: Any) -> str:
    """Get node name from a node execution (dict or model)."""
    if isinstance(node, dict):
        return node["node_name"]
    return node.node_name


# ---------------------------------------------------------------------------
# Core assertions (task-015)
# ---------------------------------------------------------------------------


def node_was_visited(trace: Any, node_name: str) -> None:
    """Assert that a node was visited during execution."""
    visited = _get_node_names(trace)
    if node_name not in visited:
        raise AssertionError(f"Node '{node_name}' was NOT visited.\nVisited nodes: {visited}")


def node_was_not_visited(trace: Any, node_name: str) -> None:
    """Assert that a node was NOT visited during execution."""
    visited = _get_node_names(trace)
    if node_name in visited:
        raise AssertionError(
            f"Node '{node_name}' WAS visited but should not have been.\nVisited nodes: {visited}"
        )


def node_visited_before(trace: Any, node_a: str, node_b: str) -> None:
    """Assert that node_a was visited before node_b."""
    visited = _get_node_names(trace)
    if node_a not in visited:
        raise AssertionError(f"Node '{node_a}' was NOT visited.\nVisited nodes: {visited}")
    if node_b not in visited:
        raise AssertionError(f"Node '{node_b}' was NOT visited.\nVisited nodes: {visited}")
    idx_a = visited.index(node_a)
    idx_b = visited.index(node_b)
    if idx_a >= idx_b:
        raise AssertionError(
            f"Node '{node_a}' (position {idx_a}) was NOT visited before "
            f"'{node_b}' (position {idx_b}).\n"
            f"Execution order: {visited}"
        )


def edge_taken(trace: Any, from_node: str, to_node: str) -> None:
    """Assert that a specific edge transition occurred."""
    edges = _get_edges(trace)
    if (from_node, to_node) not in edges:
        edge_strs = [f"{f} -> {t}" for f, t in edges]
        raise AssertionError(
            f"Edge '{from_node}' -> '{to_node}' was NOT taken.\nEdges taken: {edge_strs}"
        )


def no_errors(trace: Any) -> None:
    """Assert that no nodes had errors during execution."""
    nodes = _get_nodes(trace)
    errored = [_get_node_name(n) for n in nodes if _get_node_status(n) == "error"]
    if errored:
        raise AssertionError(
            f"Expected no errors, but {len(errored)} node(s) had errors: {errored}"
        )


def total_nodes_visited(
    trace: Any,
    min: Optional[int] = None,
    max: Optional[int] = None,
) -> None:
    """Assert that the total number of visited nodes is within [min, max]."""
    visited = _get_node_names(trace)
    count = len(visited)
    if min is not None and count < min:
        raise AssertionError(
            f"Expected at least {min} nodes visited, but got {count}.\nVisited nodes: {visited}"
        )
    if max is not None and count > max:
        raise AssertionError(
            f"Expected at most {max} nodes visited, but got {count}.\nVisited nodes: {visited}"
        )


# ---------------------------------------------------------------------------
# Advanced assertions (task-016)
# ---------------------------------------------------------------------------


def _get_node_by_name(trace: Any, node_name: str) -> Any:
    """Get a node execution by name, raising if not found."""
    if isinstance(trace, dict):
        for n in trace.get("nodes", []):
            if n["node_name"] == node_name:
                return n
    else:
        node = trace.get_node(node_name)
        if node is not None:
            return node
    raise AssertionError(
        f"Node '{node_name}' was NOT visited.\nVisited nodes: {_get_node_names(trace)}"
    )


def state_at_node(
    trace: Any,
    node_name: str,
    predicate: Any,
) -> None:
    """Assert that a predicate holds on the output state of a node.

    The predicate receives the node's state_after (Trace) or output (dict)
    and should return True/False or raise an exception.
    """
    node = _get_node_by_name(trace, node_name)
    if isinstance(node, dict):
        state = node.get("output", {})
    else:
        state = node.state_after

    result = predicate(state)
    if result is False:
        raise AssertionError(f"State predicate failed for node '{node_name}'.\nState: {state}")


def max_duration(trace: Any, node_name: str, ms: float) -> None:
    """Assert that a node executed within the given time limit (ms)."""
    node = _get_node_by_name(trace, node_name)
    if isinstance(node, dict):
        actual = node.get("duration_ms", 0)
    else:
        actual = node.duration_ms

    if actual > ms:
        raise AssertionError(
            f"Node '{node_name}' took {actual:.1f}ms, exceeding limit of {ms:.1f}ms."
        )
