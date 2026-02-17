# Getting Started

## Installation

```bash
pip install agentrace
```

For development:

```bash
pip install agentrace[dev]
```

## Basic Usage

### 1. Wrap your LangGraph agent

```python
from agentrace import wrap

# Your existing compiled LangGraph
graph = builder.compile()

# Wrap it with agentrace (1 line)
traced = wrap(graph)
```

### 2. Run and get a trace

```python
result = traced.invoke({"query": "What is LangGraph?"})
trace = traced.last_trace
```

The `trace` object is a Pydantic model containing the complete execution record.

### 3. Print a terminal report

```python
from agentrace import print_trace

# Summary view
print_trace(trace)

# Detailed view with state diffs
print_trace(trace, detailed=True)
```

### 4. Assert agent behavior

```python
from agentrace import assertions

assertions.node_was_visited(trace, "retriever")
assertions.node_visited_before(trace, "retriever", "generator")
assertions.edge_taken(trace, "retriever", "processor")
assertions.no_errors(trace)
assertions.total_nodes_visited(trace, min=3, max=5)
```

### 5. Generate reports

```python
# Mermaid diagram
print(trace.to_mermaid())

# HTML report
trace.to_html("report.html")

# JSON export
trace.to_json("trace.json")

# JUnit XML (for CI/CD)
trace.to_junit_xml("results.xml")
```

## Using with pytest

agentrace includes a pytest plugin that auto-registers when installed.

```python
def test_my_agent(traced_agent):
    from agentrace import assertions

    traced = traced_agent(my_compiled_graph)
    traced.invoke({"query": "test"})
    trace = traced.last_trace

    assertions.node_was_visited(trace, "retriever")
    assertions.no_errors(trace)
```

The `traced_agent` fixture is a factory that creates traced wrappers for your graphs.

## Stream mode

agentrace also supports LangGraph's stream mode:

```python
traced = wrap(graph)
for chunk in traced.stream({"query": "hello"}):
    print(chunk)

trace = traced.last_trace  # trace is captured after streaming
```

## Legacy capture API

For simple use cases, the stream-based `capture()` function is also available:

```python
from agentrace import capture

result = capture(graph, {"query": "hello"})
print(result["node_names"])  # ['retriever', 'processor', 'generator']
```
