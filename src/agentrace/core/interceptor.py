"""LangChain callback handler for capturing LangGraph traces."""

import time
from typing import Any, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from agentrace.core.differ import compute_state_diff
from agentrace.core.models import (
    EdgeTransition,
    NodeExecution,
    NodeStatus,
    RunMetadata,
    Trace,
)


class TraceInterceptor(BaseCallbackHandler):
    """Callback handler that captures a structured Trace from a LangGraph run.

    Attach via: ``graph.invoke(input, config={"callbacks": [handler]})``

    Key insight: ``on_chain_start`` receives ``metadata["langgraph_node"]`` for
    node-level events, but ``on_chain_end`` and ``on_chain_error`` do NOT.
    We track ``run_id -> node_name`` from start events to correlate.
    """

    def __init__(self) -> None:
        super().__init__()
        self.trace = Trace()
        self._accumulated_state: dict[str, Any] = {}
        self._node_starts: dict[str, float] = {}  # run_id -> start time
        self._node_state_before: dict[str, dict[str, Any]] = {}  # run_id -> state snapshot
        self._node_names: dict[str, str] = {}  # run_id -> node name
        self._node_metadata: dict[str, dict[str, Any]] = {}  # run_id -> metadata
        self._graph_run_id: Optional[str] = None
        self._last_node_name: Optional[str] = None
        self._step = 0

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        meta = metadata or {}
        node_name = meta.get("langgraph_node")

        if node_name is None and parent_run_id is None:
            # Graph-level start
            self._graph_run_id = str(run_id)
            self.trace.metadata.timestamp_start = time.perf_counter()
            self.trace.metadata.run_id = self._graph_run_id
            if isinstance(inputs, dict):
                self.trace.metadata.input_data = dict(inputs)
                self._accumulated_state = dict(inputs)
        elif node_name is not None:
            # Node-level start — record for later correlation
            rid = str(run_id)
            self._node_names[rid] = node_name
            self._node_metadata[rid] = dict(meta)
            self._node_starts[rid] = time.perf_counter()
            self._node_state_before[rid] = dict(self._accumulated_state)

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        rid = str(run_id)
        node_name = self._node_names.pop(rid, None)

        if node_name is None and parent_run_id is None:
            # Graph-level end
            self._finalize_graph(outputs)
        elif node_name is not None:
            # Node-level end
            end_time = time.perf_counter()
            start_time = self._node_starts.pop(rid, end_time)
            state_before = self._node_state_before.pop(rid, {})
            node_meta = self._node_metadata.pop(rid, {})

            # Merge output into accumulated state
            if isinstance(outputs, dict):
                self._accumulated_state.update(outputs)

            state_after = dict(self._accumulated_state)
            state_diff = compute_state_diff(state_before, state_after)

            self._step += 1
            step_num = node_meta.get("langgraph_step", self._step)

            node_exec = NodeExecution(
                node_name=node_name,
                step=step_num,
                status=NodeStatus.SUCCESS,
                state_before=state_before,
                state_after=state_after,
                state_diff=state_diff,
                timestamp_start=start_time,
                timestamp_end=end_time,
                duration_ms=(end_time - start_time) * 1000,
                run_id=rid,
                metadata=node_meta,
            )
            self.trace.nodes.append(node_exec)

            # Create edge from previous node
            if self._last_node_name is not None:
                edge = EdgeTransition(
                    from_node=self._last_node_name,
                    to_node=node_name,
                    step=step_num,
                    timestamp=end_time,
                )
                self.trace.edges.append(edge)

            self._last_node_name = node_name

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        rid = str(run_id)
        node_name = self._node_names.pop(rid, None)

        if node_name is not None:
            # Node-level error
            end_time = time.perf_counter()
            start_time = self._node_starts.pop(rid, end_time)
            state_before = self._node_state_before.pop(rid, {})
            node_meta = self._node_metadata.pop(rid, {})

            self._step += 1
            step_num = node_meta.get("langgraph_step", self._step)

            node_exec = NodeExecution(
                node_name=node_name,
                step=step_num,
                status=NodeStatus.ERROR,
                state_before=state_before,
                state_after=dict(self._accumulated_state),
                state_diff=None,
                timestamp_start=start_time,
                timestamp_end=end_time,
                duration_ms=(end_time - start_time) * 1000,
                error=str(error),
                run_id=rid,
                metadata=node_meta,
            )
            self.trace.nodes.append(node_exec)

            if self._last_node_name is not None:
                edge = EdgeTransition(
                    from_node=self._last_node_name,
                    to_node=node_name,
                    step=step_num,
                    timestamp=end_time,
                )
                self.trace.edges.append(edge)

            self._last_node_name = node_name

        elif rid == self._graph_run_id:
            # Graph-level error — finalize what we have
            self._finalize_graph(None)

    def _finalize_graph(self, outputs: Any) -> None:
        """Finalize the graph-level trace metadata."""
        end_time = time.perf_counter()
        self.trace.metadata.timestamp_end = end_time
        self.trace.metadata.duration_ms = (
            (end_time - self.trace.metadata.timestamp_start) * 1000
        )
        if isinstance(outputs, dict):
            self.trace.metadata.output_data = dict(outputs)
        self.trace.metadata.total_nodes = len(self.trace.nodes)
        self.trace.metadata.error_count = sum(
            1 for n in self.trace.nodes if n.status == NodeStatus.ERROR
        )
