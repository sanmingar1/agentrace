# Changelog

All notable changes to agentrace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Async LangGraph support (`ainvoke`, `astream`)

## [0.1.0] - 2026-02-17

### Added
- Stream-based node capture via `capture()` (Phase 1 PoC)
- Callback-based tracing via `wrap()` using `BaseCallbackHandler` (Phase 2)
- Pydantic v2 models: `Trace`, `NodeExecution`, `EdgeTransition`, `RunMetadata`
- State diffing per node via deepdiff (`compute_state_diff`)
- Rich terminal reporter (`print_trace`) with summary and detailed modes
- Mermaid diagram generator (`to_mermaid`, `trace.to_mermaid()`)
- Self-contained HTML reporter (`to_html`, `trace.to_html()`)
- JSON export (`to_json`, `trace.to_json()`)
- JUnit XML reporter for CI/CD (`to_junit_xml`, `trace.to_junit_xml()`)
- 8 assertion functions: `node_was_visited`, `node_was_not_visited`,
  `node_visited_before`, `edge_taken`, `no_errors`, `total_nodes_visited`,
  `state_at_node`, `max_duration`
- pytest plugin with `traced_agent` fixture and `@pytest.mark.agentrace` marker
- GitHub Actions CI: lint (ruff) + test matrix (Python 3.10, 3.11, 3.12)
- GitHub Actions publish workflow (PyPI trusted publishing)
- mkdocs-material documentation site
- Examples: `simple_chatbot.py`, `rag_with_routing.py`
- `py.typed` marker (PEP 561) for mypy/pyright compatibility

### Technical
- 127 tests, 90%+ code coverage
- Supports both legacy dict traces and Pydantic `Trace` objects across all APIs
- Both `invoke()` and `stream()` modes capture traces
- Error nodes captured with `NodeStatus.ERROR` even when graph raises
