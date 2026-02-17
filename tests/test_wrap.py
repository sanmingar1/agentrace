"""Tests for Phase 2: wrap() API, Trace models, differ, interceptor, and Rich reporter."""

import json

import pytest
from rich.console import Console

from agentrace import wrap, Trace, assertions, to_mermaid
from agentrace.core.models import NodeStatus, NodeExecution, EdgeTransition, RunMetadata
from agentrace.core.differ import compute_state_diff
from agentrace.reporters.terminal import print_trace
from tests.agents.simple_agent import create_simple_agent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def agent():
    return create_simple_agent()


@pytest.fixture
def traced(agent):
    return wrap(agent)


@pytest.fixture
def result_and_trace(traced):
    result = traced.invoke({"query": "test query"})
    return result, traced.last_trace


@pytest.fixture
def trace(result_and_trace):
    return result_and_trace[1]


# ---------------------------------------------------------------------------
# TracedGraph.invoke() produces a Trace
# ---------------------------------------------------------------------------

class TestTracedGraphInvoke:
    def test_invoke_returns_result(self, result_and_trace):
        result, _ = result_and_trace
        assert "response" in result
        assert result["response"].startswith("Generated answer:")

    def test_invoke_produces_trace(self, trace):
        assert isinstance(trace, Trace)

    def test_trace_has_correct_nodes(self, trace):
        assert trace.node_names == ["retriever", "processor", "generator"]

    def test_last_trace_populated(self, traced):
        assert traced.last_trace is None
        traced.invoke({"query": "hello"})
        assert traced.last_trace is not None
        assert isinstance(traced.last_trace, Trace)


# ---------------------------------------------------------------------------
# TracedGraph.stream()
# ---------------------------------------------------------------------------

class TestTracedGraphStream:
    def test_stream_yields_chunks(self, traced):
        chunks = list(traced.stream({"query": "test"}))
        assert len(chunks) > 0

    def test_stream_captures_trace(self, traced):
        list(traced.stream({"query": "test"}))
        trace = traced.last_trace
        assert isinstance(trace, Trace)
        assert len(trace.nodes) > 0


# ---------------------------------------------------------------------------
# Trace model properties
# ---------------------------------------------------------------------------

class TestTraceModel:
    def test_node_names_order(self, trace):
        assert trace.node_names == ["retriever", "processor", "generator"]

    def test_successful_property(self, trace):
        assert trace.successful is True

    def test_get_node(self, trace):
        node = trace.get_node("processor")
        assert node is not None
        assert node.node_name == "processor"

    def test_get_node_missing(self, trace):
        assert trace.get_node("nonexistent") is None

    def test_metadata_populated(self, trace):
        meta = trace.metadata
        assert meta.total_nodes == 3
        assert meta.duration_ms > 0
        assert meta.error_count == 0
        assert meta.input_data == {"query": "test query"}

    def test_nodes_have_timing(self, trace):
        for node in trace.nodes:
            assert node.duration_ms >= 0
            assert node.timestamp_end >= node.timestamp_start

    def test_nodes_have_status(self, trace):
        for node in trace.nodes:
            assert node.status == NodeStatus.SUCCESS


# ---------------------------------------------------------------------------
# State diffs
# ---------------------------------------------------------------------------

class TestStateDiff:
    def test_compute_state_diff_added(self):
        diff = compute_state_diff({"a": 1}, {"a": 1, "b": 2})
        assert diff is not None
        assert "added" in diff
        assert "b" in diff["added"]

    def test_compute_state_diff_changed(self):
        diff = compute_state_diff({"a": 1}, {"a": 2})
        assert diff is not None
        assert "changed" in diff

    def test_compute_state_diff_removed(self):
        diff = compute_state_diff({"a": 1, "b": 2}, {"a": 1})
        assert diff is not None
        assert "removed" in diff

    def test_compute_state_diff_none_when_equal(self):
        assert compute_state_diff({"a": 1}, {"a": 1}) is None

    def test_nodes_have_state_diff(self, trace):
        # At least one node should have a state diff (they all add keys)
        diffs = [n.state_diff for n in trace.nodes if n.state_diff is not None]
        assert len(diffs) > 0


# ---------------------------------------------------------------------------
# Edge transitions
# ---------------------------------------------------------------------------

class TestEdgeTransitions:
    def test_edges_created(self, trace):
        assert len(trace.edges) == 2  # retriever->processor, processor->generator

    def test_edge_order(self, trace):
        edges = trace.edges
        assert edges[0].from_node == "retriever"
        assert edges[0].to_node == "processor"
        assert edges[1].from_node == "processor"
        assert edges[1].to_node == "generator"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_node_error_captured(self):
        """A node that raises should be captured with ERROR status."""
        from typing import TypedDict
        from langgraph.graph import StateGraph, START, END

        class ErrState(TypedDict):
            value: str

        def good_node(state: ErrState) -> dict:
            return {"value": "ok"}

        def bad_node(state: ErrState) -> dict:
            raise ValueError("something went wrong")

        builder = StateGraph(ErrState)
        builder.add_node("good", good_node)
        builder.add_node("bad", bad_node)
        builder.add_edge(START, "good")
        builder.add_edge("good", "bad")
        builder.add_edge("bad", END)
        graph = builder.compile()

        traced = wrap(graph)
        with pytest.raises(ValueError, match="something went wrong"):
            traced.invoke({"value": "start"})

        trace = traced.last_trace
        assert trace is not None
        # The good node should be SUCCESS
        good = trace.get_node("good")
        assert good is not None
        assert good.status == NodeStatus.SUCCESS
        # The bad node should be ERROR
        bad = trace.get_node("bad")
        assert bad is not None
        assert bad.status == NodeStatus.ERROR
        assert "something went wrong" in bad.error


# ---------------------------------------------------------------------------
# Pydantic serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_model_dump_json(self, trace):
        json_str = trace.model_dump_json()
        data = json.loads(json_str)
        assert "metadata" in data
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 3

    def test_model_dump(self, trace):
        data = trace.model_dump()
        assert isinstance(data, dict)
        assert data["nodes"][0]["node_name"] == "retriever"


# ---------------------------------------------------------------------------
# Assertions work with Trace objects
# ---------------------------------------------------------------------------

class TestAssertionsWithTrace:
    def test_node_was_visited_with_trace(self, trace):
        assertions.node_was_visited(trace, "retriever")
        assertions.node_was_visited(trace, "processor")
        assertions.node_was_visited(trace, "generator")

    def test_node_was_visited_fails_with_trace(self, trace):
        with pytest.raises(AssertionError, match="NOT visited"):
            assertions.node_was_visited(trace, "nonexistent")

    def test_node_was_not_visited(self, trace):
        assertions.node_was_not_visited(trace, "nonexistent")

    def test_node_was_not_visited_fails(self, trace):
        with pytest.raises(AssertionError, match="WAS visited"):
            assertions.node_was_not_visited(trace, "retriever")

    def test_node_visited_before(self, trace):
        assertions.node_visited_before(trace, "retriever", "processor")
        assertions.node_visited_before(trace, "retriever", "generator")
        assertions.node_visited_before(trace, "processor", "generator")

    def test_node_visited_before_fails_wrong_order(self, trace):
        with pytest.raises(AssertionError, match="NOT visited before"):
            assertions.node_visited_before(trace, "generator", "retriever")

    def test_node_visited_before_fails_missing_node(self, trace):
        with pytest.raises(AssertionError, match="NOT visited"):
            assertions.node_visited_before(trace, "missing", "retriever")

    def test_edge_taken(self, trace):
        assertions.edge_taken(trace, "retriever", "processor")
        assertions.edge_taken(trace, "processor", "generator")

    def test_edge_taken_fails(self, trace):
        with pytest.raises(AssertionError, match="NOT taken"):
            assertions.edge_taken(trace, "retriever", "generator")

    def test_no_errors(self, trace):
        assertions.no_errors(trace)

    def test_no_errors_fails(self):
        """A trace with an errored node should fail no_errors."""
        from typing import TypedDict
        from langgraph.graph import StateGraph, START, END

        class S(TypedDict):
            v: str

        def fail_node(state: S) -> dict:
            raise RuntimeError("boom")

        builder = StateGraph(S)
        builder.add_node("fail", fail_node)
        builder.add_edge(START, "fail")
        builder.add_edge("fail", END)
        graph = builder.compile()

        traced = wrap(graph)
        with pytest.raises(RuntimeError):
            traced.invoke({"v": ""})

        with pytest.raises(AssertionError, match="1 node.*had errors"):
            assertions.no_errors(traced.last_trace)

    def test_total_nodes_visited_exact(self, trace):
        assertions.total_nodes_visited(trace, min=3, max=3)

    def test_total_nodes_visited_range(self, trace):
        assertions.total_nodes_visited(trace, min=1, max=10)

    def test_total_nodes_visited_min_only(self, trace):
        assertions.total_nodes_visited(trace, min=2)

    def test_total_nodes_visited_max_only(self, trace):
        assertions.total_nodes_visited(trace, max=5)

    def test_total_nodes_visited_fails_min(self, trace):
        with pytest.raises(AssertionError, match="at least 10"):
            assertions.total_nodes_visited(trace, min=10)

    def test_total_nodes_visited_fails_max(self, trace):
        with pytest.raises(AssertionError, match="at most 1"):
            assertions.total_nodes_visited(trace, max=1)

    # --- Advanced assertions (task-016) ---

    def test_state_at_node(self, trace):
        assertions.state_at_node(
            trace, "retriever",
            lambda s: "documents" in s,
        )

    def test_state_at_node_fails(self, trace):
        with pytest.raises(AssertionError, match="State predicate failed"):
            assertions.state_at_node(
                trace, "retriever",
                lambda s: "nonexistent_key" in s,
            )

    def test_state_at_node_missing_node(self, trace):
        with pytest.raises(AssertionError, match="NOT visited"):
            assertions.state_at_node(trace, "missing", lambda s: True)

    def test_max_duration(self, trace):
        # Our mock nodes are very fast, 1000ms should be plenty
        assertions.max_duration(trace, "retriever", ms=1000)

    def test_max_duration_fails(self, trace):
        # 0ms is impossible to beat
        with pytest.raises(AssertionError, match="exceeding limit"):
            assertions.max_duration(trace, "retriever", ms=0)


# ---------------------------------------------------------------------------
# Mermaid diagram generator
# ---------------------------------------------------------------------------

class TestMermaidGenerator:
    def test_to_mermaid_basic(self, trace):
        mermaid = to_mermaid(trace)
        assert mermaid.startswith("graph TD")
        assert "retriever" in mermaid
        assert "processor" in mermaid
        assert "generator" in mermaid

    def test_to_mermaid_contains_edges(self, trace):
        mermaid = to_mermaid(trace)
        assert "retriever --> processor" in mermaid
        assert "processor --> generator" in mermaid

    def test_to_mermaid_contains_start_end(self, trace):
        mermaid = to_mermaid(trace)
        assert "START" in mermaid
        assert "END" in mermaid

    def test_to_mermaid_contains_timing(self, trace):
        mermaid = to_mermaid(trace)
        assert "ms" in mermaid

    def test_to_mermaid_contains_styles(self, trace):
        mermaid = to_mermaid(trace)
        assert "style retriever" in mermaid
        assert "#28a745" in mermaid  # success green

    def test_to_mermaid_lr_direction(self, trace):
        mermaid = to_mermaid(trace, direction="LR")
        assert mermaid.startswith("graph LR")

    def test_trace_to_mermaid_method(self, trace):
        mermaid = trace.to_mermaid()
        assert "graph TD" in mermaid
        assert "retriever" in mermaid

    def test_to_mermaid_error_node_style(self):
        """Errored nodes should have red styling."""
        from typing import TypedDict
        from langgraph.graph import StateGraph, START, END

        class S(TypedDict):
            v: str

        def fail_node(state: S) -> dict:
            raise RuntimeError("boom")

        builder = StateGraph(S)
        builder.add_node("fail", fail_node)
        builder.add_edge(START, "fail")
        builder.add_edge("fail", END)
        graph = builder.compile()

        traced = wrap(graph)
        with pytest.raises(RuntimeError):
            traced.invoke({"v": ""})

        mermaid = to_mermaid(traced.last_trace)
        assert "#dc3545" in mermaid  # error red


# ---------------------------------------------------------------------------
# Rich reporter
# ---------------------------------------------------------------------------

class TestRichReporter:
    def test_print_trace_runs(self, trace):
        console = Console(file=None, force_terminal=True, width=120)
        # Should not raise
        print_trace(trace, console=console)

    def test_print_trace_detailed(self, trace):
        console = Console(file=None, force_terminal=True, width=120)
        # Should not raise
        print_trace(trace, detailed=True, console=console)

    def test_print_trace_dict_still_works(self):
        """Legacy dict traces should still render."""
        from agentrace import capture
        agent = create_simple_agent()
        dict_trace = capture(agent, {"query": "test"})
        console = Console(file=None, force_terminal=True, width=120)
        print_trace(dict_trace, console=console)
