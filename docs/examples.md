# Examples

## Simple Chatbot

A basic 3-node chatbot demonstrating tracing, assertions, and reporting.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from agentrace import wrap, assertions, print_trace


class ChatState(TypedDict):
    query: str
    context: str
    response: str


def retrieve(state: ChatState) -> dict:
    return {"context": f"Relevant docs for: {state['query']}"}

def generate(state: ChatState) -> dict:
    return {"response": f"Answer based on: {state['context']}"}

def postprocess(state: ChatState) -> dict:
    return {"response": state["response"].strip()}


builder = StateGraph(ChatState)
builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)
builder.add_node("postprocess", postprocess)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", "postprocess")
builder.add_edge("postprocess", END)
graph = builder.compile()

# Trace and assert
traced = wrap(graph)
result = traced.invoke({"query": "What is agentrace?", "context": "", "response": ""})
trace = traced.last_trace

print_trace(trace, detailed=True)
assertions.no_errors(trace)
assertions.node_visited_before(trace, "retrieve", "generate")
print(trace.to_mermaid())
```

## RAG Agent with Conditional Routing

An agent that routes queries to different handlers based on classification.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from agentrace import wrap, assertions, print_trace


class RAGState(TypedDict):
    query: str
    intent: str
    documents: list[str]
    response: str


def classify_intent(state: RAGState) -> dict:
    query = state["query"].lower()
    if "code" in query or "how to" in query:
        return {"intent": "technical"}
    elif "what is" in query:
        return {"intent": "factual"}
    return {"intent": "conversational"}

def technical_retriever(state: RAGState) -> dict:
    return {"documents": ["api_docs.md", "tutorial.py"]}

def factual_retriever(state: RAGState) -> dict:
    return {"documents": ["wiki_article.md"]}

def conversational_handler(state: RAGState) -> dict:
    return {"documents": [], "response": f"Hello! {state['query']}"}

def generate_response(state: RAGState) -> dict:
    docs = ", ".join(state["documents"])
    return {"response": f"Based on [{docs}]: Answer to '{state['query']}'"}

def route_by_intent(state: RAGState) -> str:
    return {
        "technical": "technical_retriever",
        "factual": "factual_retriever",
    }.get(state.get("intent", ""), "conversational_handler")


builder = StateGraph(RAGState)
builder.add_node("classify_intent", classify_intent)
builder.add_node("technical_retriever", technical_retriever)
builder.add_node("factual_retriever", factual_retriever)
builder.add_node("conversational_handler", conversational_handler)
builder.add_node("generate_response", generate_response)

builder.add_edge(START, "classify_intent")
builder.add_conditional_edges("classify_intent", route_by_intent)
builder.add_edge("technical_retriever", "generate_response")
builder.add_edge("factual_retriever", "generate_response")
builder.add_edge("conversational_handler", END)
builder.add_edge("generate_response", END)
graph = builder.compile()

# Run different queries
traced = wrap(graph)

for query in ["How to use agentrace?", "What is LangGraph?", "Hello!"]:
    result = traced.invoke({
        "query": query, "intent": "", "documents": [], "response": ""
    })
    trace = traced.last_trace
    print_trace(trace)
    assertions.node_was_visited(trace, "classify_intent")
    assertions.no_errors(trace)
```

## Testing with pytest

```python
# test_my_agent.py
import pytest
from agentrace import assertions


def test_technical_routing(traced_agent):
    """Test that technical queries route correctly."""
    traced = traced_agent(my_graph)
    traced.invoke({"query": "How to code?", "intent": "", "documents": [], "response": ""})
    trace = traced.last_trace

    assertions.node_was_visited(trace, "classify_intent")
    assertions.node_was_visited(trace, "technical_retriever")
    assertions.node_was_not_visited(trace, "factual_retriever")
    assertions.no_errors(trace)


def test_performance(traced_agent):
    """Test that nodes execute within time limits."""
    traced = traced_agent(my_graph)
    traced.invoke({"query": "Quick question", "intent": "", "documents": [], "response": ""})
    trace = traced.last_trace

    assertions.max_duration(trace, "classify_intent", ms=100)


def test_state_changes(traced_agent):
    """Test that nodes produce expected state changes."""
    traced = traced_agent(my_graph)
    traced.invoke({"query": "What is X?", "intent": "", "documents": [], "response": ""})
    trace = traced.last_trace

    assertions.state_at_node(trace, "factual_retriever", lambda s: len(s["documents"]) > 0)
```

## Generating Reports

```python
from agentrace import wrap

traced = wrap(graph)
traced.invoke(input_data)
trace = traced.last_trace

# Terminal
from agentrace import print_trace
print_trace(trace, detailed=True)

# HTML (open in browser)
trace.to_html("report.html")

# Mermaid (paste into GitHub markdown)
print(trace.to_mermaid())

# JSON (for programmatic analysis)
trace.to_json("trace.json")

# JUnit XML (for CI/CD)
trace.to_junit_xml("results.xml")
```
