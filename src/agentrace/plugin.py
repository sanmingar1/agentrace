"""Pytest plugin for agentrace.

Provides fixtures and markers for testing LangGraph agents with tracing.

Usage:
    def test_my_agent(traced_agent):
        graph = create_my_agent()
        traced = traced_agent(graph)
        traced.invoke({"query": "hello"})
        trace = traced.last_trace
        assertions.node_was_visited(trace, "retriever")
"""

import pytest

from agentrace.core.wrapper import wrap, TracedGraph
from agentrace.reporters.terminal import print_trace


def pytest_configure(config):
    """Register the agentrace marker."""
    config.addinivalue_line(
        "markers",
        "agentrace: mark test as an agentrace agent test",
    )


@pytest.fixture
def traced_agent():
    """Fixture that returns a factory for creating traced agents.

    Usage:
        def test_something(traced_agent):
            traced = traced_agent(my_compiled_graph)
            result = traced.invoke({"query": "test"})
            trace = traced.last_trace
    """
    _instances: list[TracedGraph] = []

    def _factory(graph):
        traced = wrap(graph)
        _instances.append(traced)
        return traced

    yield _factory


@pytest.fixture
def agentrace_report(request, capsys):
    """Fixture that auto-prints trace report after test completes.

    Usage:
        def test_something(traced_agent, agentrace_report):
            traced = traced_agent(my_compiled_graph)
            traced.invoke({"query": "test"})
            agentrace_report(traced.last_trace)
    """
    _traces: list = []

    def _collect(trace):
        _traces.append(trace)

    yield _collect

    # Print reports for collected traces after test
    if _traces:
        for trace in _traces:
            print_trace(trace)
