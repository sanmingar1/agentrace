"""Tests for the HTML reporter."""

import os
import tempfile

import pytest

from agentrace import capture, to_html, wrap
from tests.agents.routing_agent import create_routing_agent
from tests.agents.simple_agent import create_simple_agent


@pytest.fixture
def trace():
    graph = create_simple_agent()
    traced = wrap(graph)
    traced.invoke({"query": "test"})
    return traced.last_trace


class TestHtmlReporter:
    def test_generates_html_string(self, trace):
        html = to_html(trace)
        assert "<!DOCTYPE html>" in html
        assert "agentrace Report" in html

    def test_contains_node_names(self, trace):
        html = to_html(trace)
        assert "retriever" in html
        assert "processor" in html
        assert "generator" in html

    def test_contains_mermaid(self, trace):
        html = to_html(trace)
        assert "mermaid" in html
        assert "graph TD" in html

    def test_contains_stats(self, trace):
        html = to_html(trace)
        assert "SUCCESS" in html
        assert "Nodes Visited" in html
        assert "Total Duration" in html

    def test_contains_node_cards(self, trace):
        html = to_html(trace)
        assert "node-card" in html
        assert "Step 1" in html

    def test_writes_to_file(self, trace):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            to_html(trace, output_path=path)
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "agentrace Report" in content
        finally:
            os.unlink(path)

    def test_trace_to_html_method(self, trace):
        html = trace.to_html()
        assert "<!DOCTYPE html>" in html
        assert "retriever" in html

    def test_trace_to_html_writes_file(self, trace):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            trace.to_html(output_path=path)
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_error_trace_html(self):
        from typing import TypedDict

        from langgraph.graph import END, START, StateGraph

        class S(TypedDict):
            v: str

        def bad(state: S) -> dict:
            raise ValueError("boom")

        builder = StateGraph(S)
        builder.add_node("bad", bad)
        builder.add_edge(START, "bad")
        builder.add_edge("bad", END)
        graph = builder.compile()

        traced = wrap(graph)
        with pytest.raises(ValueError):
            traced.invoke({"v": ""})

        html = to_html(traced.last_trace)
        assert "FAILED" in html
        assert "boom" in html

    def test_dict_trace_html(self):
        graph = create_simple_agent()
        dict_trace = capture(graph, {"query": "test"})
        html = to_html(dict_trace)
        assert "<!DOCTYPE html>" in html
        assert "retriever" in html

    def test_routing_agent_html(self):
        graph = create_routing_agent()
        traced = wrap(graph)
        traced.invoke({
            "query": "technical question",
            "category": "",
            "documents": [],
            "response": "",
        })
        html = to_html(traced.last_trace)
        assert "classifier" in html
        assert "technical_handler" in html
