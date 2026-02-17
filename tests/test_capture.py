"""Tests for agentrace capture, reporter, and assertions (PoC)."""

import io

import pytest
from rich.console import Console

from agentrace import assertions, capture, print_trace
from tests.agents.simple_agent import create_simple_agent


@pytest.fixture
def agent():
    return create_simple_agent()


@pytest.fixture
def trace(agent):
    return capture(agent, {"query": "test query"})


class TestCapture:
    def test_capture_returns_trace(self, trace):
        assert "input" in trace
        assert "output" in trace
        assert "nodes" in trace
        assert "node_names" in trace
        assert "total_duration_ms" in trace

    def test_node_names_in_order(self, trace):
        assert trace["node_names"] == ["retriever", "processor", "generator"]

    def test_nodes_have_required_fields(self, trace):
        for node in trace["nodes"]:
            assert "node_name" in node
            assert "output" in node
            assert "duration_ms" in node
            assert "step" in node
            assert node["duration_ms"] >= 0

    def test_step_numbers_sequential(self, trace):
        steps = [n["step"] for n in trace["nodes"]]
        assert steps == [1, 2, 3]

    def test_total_duration_positive(self, trace):
        assert trace["total_duration_ms"] > 0

    def test_output_contains_final_state(self, trace):
        assert "response" in trace["output"]
        assert trace["output"]["response"].startswith("Generated answer:")

    def test_input_preserved(self, trace):
        assert trace["input"] == {"query": "test query"}


class TestTerminalReporter:
    def test_print_trace_runs(self, trace):
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False, width=120)
        print_trace(trace, console=console)
        output = buf.getvalue()
        assert "agentrace" in output
        assert "retriever" in output
        assert "processor" in output
        assert "generator" in output
        assert "SUCCESS" in output


class TestAssertions:
    def test_node_was_visited_passes(self, trace):
        assertions.node_was_visited(trace, "retriever")
        assertions.node_was_visited(trace, "processor")
        assertions.node_was_visited(trace, "generator")

    def test_node_was_visited_fails_for_missing_node(self, trace):
        with pytest.raises(AssertionError, match="NOT visited"):
            assertions.node_was_visited(trace, "nonexistent_node")

    def test_node_was_visited_error_shows_visited_nodes(self, trace):
        with pytest.raises(AssertionError, match="retriever"):
            assertions.node_was_visited(trace, "missing")
