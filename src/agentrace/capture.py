"""Stream-based trace capture for LangGraph agents (PoC).

Uses LangGraph's .stream(stream_mode="updates") to capture node executions.
This is the quick PoC approach — Phase 2 will migrate to BaseCallbackHandler.
"""

import time
from typing import Any


def capture(graph: Any, input_data: dict) -> dict:
    """Capture a trace from a LangGraph compiled graph execution.

    Args:
        graph: A compiled LangGraph StateGraph.
        input_data: The input dict to pass to the graph.

    Returns:
        A TraceResult dict with keys:
            - input: the original input
            - output: accumulated final state
            - nodes: list of NodeExecution dicts
            - node_names: ordered list of visited node names
            - total_duration_ms: total execution time
    """
    nodes: list[dict] = []
    output_state: dict = dict(input_data)
    step = 0

    trace_start = time.perf_counter()

    for chunk in graph.stream(input_data, stream_mode="updates"):
        node_end = time.perf_counter()

        for node_name, node_output in chunk.items():
            step += 1
            # We can't measure exact node start from stream events,
            # so we approximate: start = previous node's end (or trace start)
            if nodes:
                node_start = nodes[-1]["timestamp_end"]
            else:
                node_start = trace_start

            duration_ms = (node_end - node_start) * 1000

            nodes.append({
                "node_name": node_name,
                "output": node_output,
                "timestamp_start": node_start,
                "timestamp_end": node_end,
                "duration_ms": duration_ms,
                "step": step,
            })

            # Accumulate state
            if isinstance(node_output, dict):
                output_state.update(node_output)

    trace_end = time.perf_counter()
    total_duration_ms = (trace_end - trace_start) * 1000

    return {
        "input": input_data,
        "output": output_state,
        "nodes": nodes,
        "node_names": [n["node_name"] for n in nodes],
        "total_duration_ms": total_duration_ms,
    }
