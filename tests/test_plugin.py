"""Tests for the agentrace pytest plugin."""

import pytest

from agentrace import assertions
from agentrace.core.models import Trace
from tests.agents.simple_agent import create_simple_agent


class TestTracedAgentFixture:
    def test_traced_agent_returns_traced_graph(self, traced_agent):
        graph = create_simple_agent()
        traced = traced_agent(graph)
        assert hasattr(traced, "invoke")
        assert hasattr(traced, "last_trace")

    def test_traced_agent_invoke_produces_trace(self, traced_agent):
        graph = create_simple_agent()
        traced = traced_agent(graph)
        result = traced.invoke({"query": "test"})
        assert "response" in result
        trace = traced.last_trace
        assert isinstance(trace, Trace)
        assert trace.node_names == ["retriever", "processor", "generator"]

    def test_traced_agent_with_assertions(self, traced_agent):
        graph = create_simple_agent()
        traced = traced_agent(graph)
        traced.invoke({"query": "hello"})
        trace = traced.last_trace
        assertions.node_was_visited(trace, "retriever")
        assertions.no_errors(trace)
        assertions.total_nodes_visited(trace, min=3, max=3)

    def test_traced_agent_multiple_graphs(self, traced_agent):
        g1 = create_simple_agent()
        g2 = create_simple_agent()
        t1 = traced_agent(g1)
        t2 = traced_agent(g2)
        t1.invoke({"query": "q1"})
        t2.invoke({"query": "q2"})
        assert t1.last_trace is not None
        assert t2.last_trace is not None


class TestAgentraceReportFixture:
    def test_report_collects_trace(self, traced_agent, agentrace_report):
        graph = create_simple_agent()
        traced = traced_agent(graph)
        traced.invoke({"query": "test"})
        # Should not raise
        agentrace_report(traced.last_trace)


@pytest.mark.agentrace
class TestAgentraceMarker:
    def test_marked_test_runs(self, traced_agent):
        graph = create_simple_agent()
        traced = traced_agent(graph)
        traced.invoke({"query": "test"})
        assertions.no_errors(traced.last_trace)
