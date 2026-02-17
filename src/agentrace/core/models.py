"""Pydantic models for agentrace traces."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class NodeStatus(str, Enum):
    """Status of a node execution."""

    SUCCESS = "success"
    ERROR = "error"


class NodeExecution(BaseModel):
    """Record of a single node execution within a graph run."""

    node_name: str
    step: int
    status: NodeStatus = NodeStatus.SUCCESS
    state_before: dict[str, Any] = Field(default_factory=dict)
    state_after: dict[str, Any] = Field(default_factory=dict)
    state_diff: Optional[dict[str, Any]] = None
    timestamp_start: float = 0.0
    timestamp_end: float = 0.0
    duration_ms: float = 0.0
    error: Optional[str] = None
    run_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EdgeTransition(BaseModel):
    """Record of a transition between two nodes."""

    from_node: str
    to_node: str
    step: int
    triggers: list[str] = Field(default_factory=list)
    timestamp: float = 0.0


class RunMetadata(BaseModel):
    """Metadata for an entire graph run."""

    run_id: Optional[str] = None
    timestamp_start: float = 0.0
    timestamp_end: float = 0.0
    duration_ms: float = 0.0
    graph_name: Optional[str] = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    total_nodes: int = 0
    error_count: int = 0


class Trace(BaseModel):
    """Complete trace of a graph execution."""

    metadata: RunMetadata = Field(default_factory=RunMetadata)
    nodes: list[NodeExecution] = Field(default_factory=list)
    edges: list[EdgeTransition] = Field(default_factory=list)

    @property
    def node_names(self) -> list[str]:
        """Ordered list of visited node names."""
        return [n.node_name for n in self.nodes]

    @property
    def successful(self) -> bool:
        """True if all nodes completed successfully."""
        return all(n.status == NodeStatus.SUCCESS for n in self.nodes)

    def get_node(self, name: str) -> Optional[NodeExecution]:
        """Get first node execution by name, or None."""
        for n in self.nodes:
            if n.node_name == name:
                return n
        return None

    def to_mermaid(self, direction: str = "TD") -> str:
        """Generate a Mermaid flowchart diagram of this trace."""
        from agentrace.reporters.mermaid import to_mermaid

        return to_mermaid(self, direction=direction)

    def to_html(self, output_path: Optional[str] = None) -> str:
        """Generate a self-contained HTML report of this trace."""
        from agentrace.reporters.html import to_html

        return to_html(self, output_path=output_path)

    def to_json(self, output_path: Optional[str] = None, indent: int = 2) -> str:
        """Export this trace as JSON."""
        from agentrace.reporters.json_reporter import to_json

        return to_json(self, output_path=output_path, indent=indent)

    def to_junit_xml(self, output_path: Optional[str] = None) -> str:
        """Generate JUnit XML report of this trace."""
        from agentrace.reporters.junit import to_junit_xml

        return to_junit_xml(self, output_path=output_path)
