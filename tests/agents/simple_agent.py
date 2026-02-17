"""Simple 3-node test agent for agentrace PoC.

Graph: retriever -> processor -> generator

All nodes are mock functions (no LLM calls).
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class AgentState(TypedDict):
    query: str
    documents: list[str]
    processed: list[str]
    response: str


def retriever(state: AgentState) -> dict:
    """Mock retriever: generates fake documents based on query."""
    query = state["query"]
    docs = [
        f"Document 1 about {query}",
        f"Document 2 about {query}",
        f"Document 3 about {query}",
    ]
    return {"documents": docs}


def processor(state: AgentState) -> dict:
    """Mock processor: transforms retrieved documents."""
    processed = [doc.upper() for doc in state["documents"]]
    return {"processed": processed}


def generator(state: AgentState) -> dict:
    """Mock generator: produces a response from processed documents."""
    summary = " | ".join(state["processed"])
    return {"response": f"Generated answer: {summary}"}


def create_simple_agent():
    """Create and compile the simple 3-node test agent."""
    builder = StateGraph(AgentState)

    builder.add_node("retriever", retriever)
    builder.add_node("processor", processor)
    builder.add_node("generator", generator)

    builder.add_edge(START, "retriever")
    builder.add_edge("retriever", "processor")
    builder.add_edge("processor", "generator")
    builder.add_edge("generator", END)

    return builder.compile()


if __name__ == "__main__":
    agent = create_simple_agent()
    result = agent.invoke({"query": "LangGraph tracing"})
    print(f"Query: {result['query']}")
    print(f"Documents: {result['documents']}")
    print(f"Processed: {result['processed']}")
    print(f"Response: {result['response']}")
