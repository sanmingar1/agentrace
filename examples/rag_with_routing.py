"""Example: RAG agent with conditional routing.

Demonstrates how agentrace traces conditional edges and branching logic.
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agentrace import wrap, assertions, print_trace, to_mermaid


# 1. Define state
class RAGState(TypedDict):
    query: str
    intent: str
    documents: list[str]
    response: str


# 2. Define nodes
def classify_intent(state: RAGState) -> dict:
    """Classify the user's intent."""
    query = state["query"].lower()
    if "code" in query or "how to" in query:
        return {"intent": "technical"}
    elif "what is" in query or "explain" in query:
        return {"intent": "factual"}
    return {"intent": "conversational"}


def technical_retriever(state: RAGState) -> dict:
    """Retrieve technical documentation."""
    return {"documents": ["api_docs.md", "tutorial.py", "examples/"]}


def factual_retriever(state: RAGState) -> dict:
    """Retrieve factual/knowledge base documents."""
    return {"documents": ["wiki_article.md", "faq.md"]}


def conversational_handler(state: RAGState) -> dict:
    """Handle conversational queries directly."""
    return {
        "documents": [],
        "response": f"Let me help you with: {state['query']}",
    }


def generate_response(state: RAGState) -> dict:
    """Generate response from retrieved documents."""
    docs = ", ".join(state["documents"])
    return {"response": f"Based on [{docs}]: Answer to '{state['query']}'"}


# 3. Routing function
def route_by_intent(state: RAGState) -> str:
    intent = state.get("intent", "conversational")
    return {
        "technical": "technical_retriever",
        "factual": "factual_retriever",
        "conversational": "conversational_handler",
    }.get(intent, "conversational_handler")


# 4. Build graph with conditional routing
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

# 5. Run three different queries to show routing
queries = [
    "How to use agentrace?",        # -> technical route
    "What is LangGraph?",           # -> factual route
    "Hello, nice to meet you!",     # -> conversational route
]

traced = wrap(graph)

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print("=" * 60)

    result = traced.invoke({
        "query": query,
        "intent": "",
        "documents": [],
        "response": "",
    })
    trace = traced.last_trace

    # Show trace
    print_trace(trace)

    # Show which route was taken
    print(f"Route taken: {trace.node_names}")
    print(f"Response: {result['response']}")

    # Common assertions
    assertions.node_was_visited(trace, "classify_intent")
    assertions.no_errors(trace)

# 6. Show Mermaid for last trace
print(f"\n{'='*60}")
print("Mermaid diagram (last trace):")
print("=" * 60)
print(to_mermaid(traced.last_trace))
