# API Reference

## Core Functions

### `wrap(graph)`

Wraps a compiled LangGraph with tracing instrumentation.

```python
from agentrace import wrap

traced = wrap(compiled_graph)
result = traced.invoke(input_data)
trace = traced.last_trace
```

**Parameters:**

- `graph` — A compiled LangGraph (`CompiledStateGraph`)

**Returns:** `TracedGraph` object with `.invoke()`, `.stream()`, and `.last_trace`

---

### `capture(graph, input_data)`

Stream-based capture (Phase 1 API). Runs the graph and returns a dict trace.

```python
from agentrace import capture

result = capture(graph, {"query": "hello"})
```

**Returns:** Dict with keys: `input`, `output`, `nodes`, `node_names`, `total_duration_ms`

---

## Reporter Functions

### `print_trace(trace, detailed=False, console=None)`

Print a rich terminal report.

```python
from agentrace import print_trace

print_trace(trace)                # summary
print_trace(trace, detailed=True) # with state diffs + timing table
```

---

### `to_mermaid(trace, direction="TD")`

Generate a Mermaid flowchart string.

```python
from agentrace import to_mermaid

print(to_mermaid(trace))
print(to_mermaid(trace, direction="LR"))  # left-to-right
```

---

### `to_html(trace, output_path=None)`

Generate a self-contained HTML report.

```python
from agentrace import to_html

html = to_html(trace)                        # returns HTML string
to_html(trace, output_path="report.html")    # writes to file
```

---

### `to_json(trace, output_path=None, indent=2)`

Export trace as JSON.

```python
from agentrace import to_json

json_str = to_json(trace)
to_json(trace, output_path="trace.json")
```

---

### `to_junit_xml(trace, output_path=None)`

Generate JUnit XML for CI/CD integration.

```python
from agentrace import to_junit_xml

xml_str = to_junit_xml(trace)
to_junit_xml(trace, output_path="results.xml")
```

---

## Assertion Functions

All assertions are in the `agentrace.assertions` module. They raise `AssertionError` with actionable messages on failure.

### `node_was_visited(trace, node_name)`

Assert that a node was visited during execution.

### `node_was_not_visited(trace, node_name)`

Assert that a node was NOT visited.

### `node_visited_before(trace, node_a, node_b)`

Assert that `node_a` was visited before `node_b`.

### `edge_taken(trace, from_node, to_node)`

Assert that a specific edge transition occurred.

### `no_errors(trace)`

Assert that no nodes had errors.

### `total_nodes_visited(trace, min=None, max=None)`

Assert the total number of visited nodes is within bounds.

### `state_at_node(trace, node_name, predicate)`

Assert that a predicate holds on the output state of a node.

```python
assertions.state_at_node(trace, "retriever", lambda s: len(s["documents"]) > 0)
```

### `max_duration(trace, node_name, ms)`

Assert that a node executed within the given time limit.

```python
assertions.max_duration(trace, "llm_call", ms=5000)
```

---

## Trace Model

### `Trace`

Pydantic model containing the complete execution record.

**Properties:**

- `node_names: list[str]` — Ordered list of visited node names
- `successful: bool` — True if all nodes completed successfully
- `metadata: RunMetadata` — Run-level metadata
- `nodes: list[NodeExecution]` — Node execution records
- `edges: list[EdgeTransition]` — Edge transitions

**Methods:**

- `get_node(name) -> NodeExecution | None` — Get node by name
- `to_mermaid(direction="TD") -> str` — Generate Mermaid diagram
- `to_html(output_path=None) -> str` — Generate HTML report
- `to_json(output_path=None) -> str` — Export as JSON
- `to_junit_xml(output_path=None) -> str` — Generate JUnit XML

### `NodeExecution`

Record of a single node execution.

- `node_name: str`
- `step: int`
- `status: NodeStatus` (SUCCESS or ERROR)
- `state_before: dict`
- `state_after: dict`
- `state_diff: dict | None`
- `duration_ms: float`
- `error: str | None`

### `EdgeTransition`

Record of a transition between two nodes.

- `from_node: str`
- `to_node: str`
- `step: int`

---

## pytest Plugin

The plugin auto-registers when agentrace is installed.

### Fixtures

- **`traced_agent`** — Factory fixture: `traced = traced_agent(graph)`
- **`agentrace_report`** — Collects traces for post-test reporting

### Markers

- **`@pytest.mark.agentrace`** — Mark a test as an agentrace test
