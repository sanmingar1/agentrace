# CI/CD Integration

## GitHub Actions

agentrace generates JUnit XML reports compatible with GitHub Actions.

### Basic workflow

```yaml
name: Agent Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest --junitxml=results.xml -q
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: results.xml
```

### Generating agentrace reports in CI

Add a test that generates HTML reports as artifacts:

```python
# tests/test_agent_ci.py
import os

def test_agent_with_report(traced_agent):
    from agentrace import assertions

    traced = traced_agent(my_graph)
    traced.invoke({"query": "CI test"})
    trace = traced.last_trace

    # Generate reports
    os.makedirs("reports", exist_ok=True)
    trace.to_html("reports/trace.html")
    trace.to_json("reports/trace.json")
    trace.to_junit_xml("reports/results.xml")

    assertions.no_errors(trace)
```

Then upload the reports directory as an artifact:

```yaml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: agentrace-reports
          path: reports/
```

## JUnit XML Format

agentrace's JUnit output treats each node as a test case:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="agentrace" tests="3" failures="0" errors="0" time="0.0012">
    <testcase name="retriever" classname="agentrace.retriever" time="0.0003"/>
    <testcase name="processor" classname="agentrace.processor" time="0.0001"/>
    <testcase name="generator" classname="agentrace.generator" time="0.0002"/>
  </testsuite>
</testsuites>
```

Failed nodes appear as `<error>` elements:

```xml
<testcase name="bad_node" classname="agentrace.bad_node" time="0.0001">
  <error message="something went wrong" type="NodeExecutionError">
    something went wrong
  </error>
</testcase>
```

## JSON Export

The JSON export contains the full Pydantic model:

```json
{
  "metadata": {
    "run_id": "...",
    "duration_ms": 1.2,
    "total_nodes": 3,
    "error_count": 0
  },
  "nodes": [...],
  "edges": [...]
}
```
