"""agentrace - Transparent tracing and instrumentation for LangGraph agents."""

__version__ = "0.1.0"

from agentrace import assertions
from agentrace.capture import capture
from agentrace.core.models import Trace
from agentrace.core.wrapper import wrap
from agentrace.reporters.html import to_html
from agentrace.reporters.json_reporter import to_json
from agentrace.reporters.junit import to_junit_xml
from agentrace.reporters.mermaid import to_mermaid
from agentrace.reporters.terminal import print_trace

__all__ = [
    "capture",
    "print_trace",
    "to_mermaid",
    "to_html",
    "to_json",
    "to_junit_xml",
    "assertions",
    "Trace",
    "wrap",
]
