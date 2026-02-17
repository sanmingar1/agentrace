"""Example: Simple 3-node chatbot with agentrace.

Demonstrates basic tracing, assertions, and terminal reporting.
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agentrace import wrap, assertions, print_trace


# 1. Define state and nodes
class ChatState(TypedDict):
    query: str
    context: str
    response: str


def retrieve(state: ChatState) -> dict:
    """Simulate document retrieval."""
    return {"context": f"Relevant docs for: {state['query']}"}


def generate(state: ChatState) -> dict:
    """Simulate LLM response generation."""
    return {"response": f"Answer based on: {state['context']}"}


def postprocess(state: ChatState) -> dict:
    """Clean up and format the response."""
    return {"response": state["response"].strip()}


# 2. Build the graph
builder = StateGraph(ChatState)
builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)
builder.add_node("postprocess", postprocess)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", "postprocess")
builder.add_edge("postprocess", END)
graph = builder.compile()


# 3. Wrap with agentrace and run
traced = wrap(graph)
result = traced.invoke({"query": "What is agentrace?", "context": "", "response": ""})
trace = traced.last_trace

# 4. Print rich terminal report
print_trace(trace)
print_trace(trace, detailed=True)

# 5. Run assertions
assertions.node_was_visited(trace, "retrieve")
assertions.node_was_visited(trace, "generate")
assertions.node_visited_before(trace, "retrieve", "generate")
assertions.no_errors(trace)
assertions.total_nodes_visited(trace, min=3, max=3)

# 6. Generate Mermaid diagram
print("\n--- Mermaid Diagram ---")
print(trace.to_mermaid())

print("\nAll assertions passed!")
