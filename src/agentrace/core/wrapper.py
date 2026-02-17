"""Wrapper API for traced graph execution."""

from typing import Any, Iterator, Optional

from agentrace.core.interceptor import TraceInterceptor
from agentrace.core.models import Trace


class TracedGraph:
    """A wrapped LangGraph compiled graph that captures traces on execution."""

    def __init__(self, graph: Any) -> None:
        self._graph = graph
        self._last_trace: Optional[Trace] = None

    @property
    def last_trace(self) -> Optional[Trace]:
        """The most recent Trace captured, or None."""
        return self._last_trace

    def invoke(
        self, input_data: dict[str, Any], config: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Run the graph and capture a trace.

        Args:
            input_data: Input dict to pass to the graph.
            config: Optional LangGraph config dict. Callbacks will be merged.

        Returns:
            The graph output dict.
        """
        interceptor = TraceInterceptor()
        config = self._merge_callbacks(config, interceptor)
        try:
            result = self._graph.invoke(input_data, config=config)
        except Exception:
            self._last_trace = interceptor.trace
            raise
        self._last_trace = interceptor.trace
        return result

    def stream(
        self,
        input_data: dict[str, Any],
        config: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Iterator[Any]:
        """Stream the graph and capture a trace.

        Yields each stream chunk. After iteration completes, the trace
        is available via ``.last_trace``.
        """
        interceptor = TraceInterceptor()
        config = self._merge_callbacks(config, interceptor)
        for chunk in self._graph.stream(input_data, config=config, **kwargs):
            yield chunk
        self._last_trace = interceptor.trace

    @staticmethod
    def _merge_callbacks(
        config: Optional[dict[str, Any]], interceptor: TraceInterceptor
    ) -> dict[str, Any]:
        """Merge the interceptor into any existing callbacks in config."""
        config = dict(config) if config else {}
        existing = config.get("callbacks", [])
        config["callbacks"] = list(existing) + [interceptor]
        return config


def wrap(graph: Any) -> TracedGraph:
    """Wrap a compiled LangGraph for automatic trace capture.

    Usage::

        traced = wrap(compiled_graph)
        result = traced.invoke({"query": "hello"})
        trace = traced.last_trace
    """
    return TracedGraph(graph)
