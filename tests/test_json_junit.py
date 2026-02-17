"""Tests for JSON and JUnit XML reporters."""

import json
import os
import tempfile
import xml.etree.ElementTree as ET

import pytest

from agentrace import capture, to_json, to_junit_xml, wrap
from tests.agents.simple_agent import create_simple_agent


@pytest.fixture
def trace():
    graph = create_simple_agent()
    traced = wrap(graph)
    traced.invoke({"query": "test"})
    return traced.last_trace


# ---------------------------------------------------------------------------
# JSON reporter
# ---------------------------------------------------------------------------

class TestJsonReporter:
    def test_returns_valid_json(self, trace):
        result = to_json(trace)
        data = json.loads(result)
        assert "nodes" in data
        assert "metadata" in data

    def test_writes_to_file(self, trace):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            to_json(trace, output_path=path)
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert len(data["nodes"]) == 3
        finally:
            os.unlink(path)

    def test_dict_trace_json(self):
        graph = create_simple_agent()
        dict_trace = capture(graph, {"query": "test"})
        result = to_json(dict_trace)
        data = json.loads(result)
        assert "node_names" in data

    def test_trace_to_json_method(self, trace):
        result = trace.to_json()
        data = json.loads(result)
        assert data["nodes"][0]["node_name"] == "retriever"

    def test_custom_indent(self, trace):
        compact = to_json(trace, indent=0)
        indented = to_json(trace, indent=4)
        # indented version should be longer due to whitespace
        assert len(indented) > len(compact)


# ---------------------------------------------------------------------------
# JUnit XML reporter
# ---------------------------------------------------------------------------

class TestJunitReporter:
    def test_returns_valid_xml(self, trace):
        xml_str = to_junit_xml(trace)
        assert '<?xml version="1.0"' in xml_str
        root = ET.fromstring(xml_str)
        assert root.tag == "testsuites"

    def test_testsuite_attributes(self, trace):
        xml_str = to_junit_xml(trace)
        root = ET.fromstring(xml_str)
        suite = root.find("testsuite")
        assert suite is not None
        assert suite.get("name") == "agentrace"
        assert suite.get("tests") == "3"
        assert suite.get("errors") == "0"

    def test_testcases_present(self, trace):
        xml_str = to_junit_xml(trace)
        root = ET.fromstring(xml_str)
        suite = root.find("testsuite")
        cases = suite.findall("testcase")
        assert len(cases) == 3
        names = [c.get("name") for c in cases]
        assert "retriever" in names
        assert "processor" in names
        assert "generator" in names

    def test_writes_to_file(self, trace):
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            path = f.name
        try:
            to_junit_xml(trace, output_path=path)
            assert os.path.exists(path)
            tree = ET.parse(path)
            root = tree.getroot()
            assert root.tag == "testsuites"
        finally:
            os.unlink(path)

    def test_error_trace_junit(self):
        from typing import TypedDict

        from langgraph.graph import END, START, StateGraph

        class S(TypedDict):
            v: str

        def bad(state: S) -> dict:
            raise RuntimeError("fail")

        builder = StateGraph(S)
        builder.add_node("bad", bad)
        builder.add_edge(START, "bad")
        builder.add_edge("bad", END)
        graph = builder.compile()

        traced = wrap(graph)
        with pytest.raises(RuntimeError):
            traced.invoke({"v": ""})

        xml_str = to_junit_xml(traced.last_trace)
        root = ET.fromstring(xml_str)
        suite = root.find("testsuite")
        assert suite.get("errors") == "1"
        error_case = suite.find(".//error")
        assert error_case is not None
        assert "fail" in error_case.get("message", "")

    def test_trace_to_junit_method(self, trace):
        xml_str = trace.to_junit_xml()
        assert "agentrace" in xml_str
        root = ET.fromstring(xml_str)
        assert root.find("testsuite") is not None

    def test_dict_trace_junit(self):
        graph = create_simple_agent()
        dict_trace = capture(graph, {"query": "test"})
        xml_str = to_junit_xml(dict_trace)
        root = ET.fromstring(xml_str)
        assert root.find("testsuite").get("tests") == "3"
