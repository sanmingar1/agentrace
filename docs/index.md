# agentrace

**Debug & trace library for LangGraph agents.**

Capture, analyze, and visualize what your agent does — node by node, edge by edge.

Zero network calls. Zero paid APIs. Pure Python.

## Why agentrace?

LangGraph agents are stateful, multi-step, non-deterministic systems. When they fail, debugging is painful:

- **LangSmith** is a paid SaaS — not always available, doesn't work offline
- **Langfuse** requires running a server — overkill for local development
- **print() debugging** — what 90% of developers actually do, and it's chaos

**agentrace** is a lightweight, graph-aware debugging tool that understands LangGraph's nodes, edges, conditional routing, and state mutations natively.

## Features

| Feature | Description |
|---------|-------------|
| **One-line integration** | `traced = wrap(graph)` — that's it |
| **Rich terminal output** | Colored trace with timing and state diffs |
| **Mermaid diagrams** | Visual execution flow for READMEs and PRs |
| **HTML reports** | Self-contained interactive reports |
| **8 assertion functions** | pytest-compatible agent behavior validation |
| **pytest plugin** | Fixtures and markers for agent testing |
| **JSON/JUnit export** | CI/CD integration out of the box |
| **State diffing** | See exactly what each node changed |

## Quick install

```bash
pip install agentrace
```

## Quick example

```python
from agentrace import wrap, assertions, print_trace

traced = wrap(your_compiled_graph)
result = traced.invoke({"query": "Hello"})
trace = traced.last_trace

print_trace(trace)
assertions.no_errors(trace)
assertions.node_was_visited(trace, "retriever")
```
