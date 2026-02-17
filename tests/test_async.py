"""Tests for async LangGraph support (ainvoke, astream)."""

import pytest

from agentrace import assertions, wrap
from agentrace.core.models import NodeStatus
from tests.agents.simple_agent import create_simple_agent


@pytest.fixture
def simple_graph():
    return create_simple_agent()


@pytest.fixture
def traced_simple(simple_graph):
    return wrap(simple_graph)


# ---------------------------------------------------------------------------
# ainvoke tests
# ---------------------------------------------------------------------------


async def test_ainvoke_returns_result(traced_simple):
    result = await traced_simple.ainvoke({"query": "async test"})
    assert "response" in result
    assert "async test" in result["response"].lower()


async def test_ainvoke_captures_trace(traced_simple):
    await traced_simple.ainvoke({"query": "async trace"})
    trace = traced_simple.last_trace
    assert trace is not None


async def test_ainvoke_trace_has_nodes(traced_simple):
    await traced_simple.ainvoke({"query": "nodes"})
    trace = traced_simple.last_trace
    node_names = [n.node_name for n in trace.nodes]
    assert "retriever" in node_names
    assert "processor" in node_names
    assert "generator" in node_names


async def test_ainvoke_trace_node_count(traced_simple):
    await traced_simple.ainvoke({"query": "count"})
    trace = traced_simple.last_trace
    assert len(trace.nodes) == 3


async def test_ainvoke_trace_edges(traced_simple):
    await traced_simple.ainvoke({"query": "edges"})
    trace = traced_simple.last_trace
    assert len(trace.edges) >= 2


async def test_ainvoke_assertions_node_visited(traced_simple):
    await traced_simple.ainvoke({"query": "assertions"})
    trace = traced_simple.last_trace
    assertions.node_was_visited(trace, "retriever")
    assertions.node_was_visited(trace, "processor")
    assertions.node_was_visited(trace, "generator")


async def test_ainvoke_assertions_order(traced_simple):
    await traced_simple.ainvoke({"query": "order"})
    trace = traced_simple.last_trace
    assertions.node_visited_before(trace, "retriever", "generator")
    assertions.node_visited_before(trace, "processor", "generator")


async def test_ainvoke_no_errors(traced_simple):
    await traced_simple.ainvoke({"query": "no errors"})
    trace = traced_simple.last_trace
    assertions.no_errors(trace)


async def test_ainvoke_node_status_success(traced_simple):
    await traced_simple.ainvoke({"query": "status"})
    trace = traced_simple.last_trace
    for node in trace.nodes:
        assert node.status == NodeStatus.SUCCESS


async def test_ainvoke_metadata_populated(traced_simple):
    await traced_simple.ainvoke({"query": "metadata"})
    trace = traced_simple.last_trace
    assert trace.metadata.run_id is not None
    assert trace.metadata.duration_ms > 0
    assert trace.metadata.total_nodes == 3


async def test_ainvoke_state_at_node(traced_simple):
    await traced_simple.ainvoke({"query": "state check"})
    trace = traced_simple.last_trace
    assertions.state_at_node(trace, "processor", lambda s: "documents" in s)


async def test_ainvoke_multiple_sequential(traced_simple):
    """Each ainvoke should produce an independent trace."""
    await traced_simple.ainvoke({"query": "first"})
    trace1 = traced_simple.last_trace

    await traced_simple.ainvoke({"query": "second"})
    trace2 = traced_simple.last_trace

    assert trace1 is not trace2
    assert trace1.metadata.run_id != trace2.metadata.run_id


# ---------------------------------------------------------------------------
# astream tests
# ---------------------------------------------------------------------------


async def test_astream_yields_chunks(traced_simple):
    chunks = []
    async for chunk in traced_simple.astream({"query": "stream test"}):
        chunks.append(chunk)
    assert len(chunks) > 0


async def test_astream_captures_trace(traced_simple):
    async for _ in traced_simple.astream({"query": "stream trace"}):
        pass
    trace = traced_simple.last_trace
    assert trace is not None


async def test_astream_trace_has_nodes(traced_simple):
    async for _ in traced_simple.astream({"query": "stream nodes"}):
        pass
    trace = traced_simple.last_trace
    node_names = [n.node_name for n in trace.nodes]
    assert "retriever" in node_names
    assert "processor" in node_names
    assert "generator" in node_names


async def test_astream_no_errors(traced_simple):
    async for _ in traced_simple.astream({"query": "stream ok"}):
        pass
    trace = traced_simple.last_trace
    assertions.no_errors(trace)


async def test_astream_assertions_node_visited(traced_simple):
    async for _ in traced_simple.astream({"query": "stream assertions"}):
        pass
    trace = traced_simple.last_trace
    assertions.node_was_visited(trace, "retriever")
    assertions.node_was_visited(trace, "generator")


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


async def test_ainvoke_error_captured():
    """If a node raises, the partial trace is still captured."""
    from typing import TypedDict

    from langgraph.graph import END, START, StateGraph

    class ErrState(TypedDict):
        value: int

    def bad_node(state: ErrState) -> dict:
        raise ValueError("intentional failure")

    builder = StateGraph(ErrState)
    builder.add_node("bad_node", bad_node)
    builder.add_edge(START, "bad_node")
    builder.add_edge("bad_node", END)
    graph = builder.compile()

    traced = wrap(graph)
    with pytest.raises(ValueError, match="intentional failure"):
        await traced.ainvoke({"value": 1})

    trace = traced.last_trace
    assert trace is not None
    error_nodes = [n for n in trace.nodes if n.status == NodeStatus.ERROR]
    assert len(error_nodes) == 1
    assert error_nodes[0].node_name == "bad_node"
