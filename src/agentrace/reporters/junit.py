"""JUnit XML reporter for agentrace traces.

Generates JUnit XML output compatible with GitHub Actions, Jenkins,
and other CI/CD systems that consume test results.

Each node execution is treated as a test case within a test suite.
"""

from pathlib import Path
from typing import Any, Optional
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring


def _get_trace_info(trace: Any) -> dict:
    """Extract trace info into a plain dict."""
    if isinstance(trace, dict):
        nodes = trace.get("nodes", [])
        return {
            "name": "agentrace",
            "total_duration_s": trace.get("total_duration_ms", 0) / 1000,
            "tests": len(nodes),
            "failures": 0,
            "errors": 0,
            "nodes": [
                {
                    "name": n["node_name"],
                    "duration_s": n.get("duration_ms", 0) / 1000,
                    "status": n.get("status", "success"),
                    "error": None,
                }
                for n in nodes
            ],
        }

    error_count = sum(1 for n in trace.nodes if n.status.value == "error")
    return {
        "name": "agentrace",
        "total_duration_s": trace.metadata.duration_ms / 1000,
        "tests": len(trace.nodes),
        "failures": 0,
        "errors": error_count,
        "nodes": [
            {
                "name": n.node_name,
                "duration_s": n.duration_ms / 1000,
                "status": n.status.value,
                "error": n.error,
            }
            for n in trace.nodes
        ],
    }


def to_junit_xml(trace: Any, output_path: Optional[str] = None) -> str:
    """Generate JUnit XML from a trace.

    Args:
        trace: A Trace model or legacy dict trace.
        output_path: If provided, write XML to this file path.

    Returns:
        The XML string.
    """
    info = _get_trace_info(trace)

    testsuites = Element("testsuites")
    testsuite = SubElement(testsuites, "testsuite")
    testsuite.set("name", info["name"])
    testsuite.set("tests", str(info["tests"]))
    testsuite.set("failures", str(info["failures"]))
    testsuite.set("errors", str(info["errors"]))
    testsuite.set("time", f"{info['total_duration_s']:.4f}")

    for node in info["nodes"]:
        testcase = SubElement(testsuite, "testcase")
        testcase.set("name", node["name"])
        testcase.set("classname", f"agentrace.{node['name']}")
        testcase.set("time", f"{node['duration_s']:.4f}")

        if node["status"] == "error":
            error_elem = SubElement(testcase, "error")
            error_elem.set("message", node["error"] or "Node execution error")
            error_elem.set("type", "NodeExecutionError")
            if node["error"]:
                error_elem.text = node["error"]

    raw_xml = tostring(testsuites, encoding="unicode", xml_declaration=True)
    pretty_xml = parseString(raw_xml).toprettyxml(indent="  ")
    # Remove extra xml declaration from minidom
    lines = pretty_xml.split("\n")
    pretty_xml = "\n".join(lines[1:])  # skip minidom's declaration
    pretty_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml.strip()

    if output_path:
        Path(output_path).write_text(pretty_xml, encoding="utf-8")

    return pretty_xml
