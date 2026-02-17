"""Test agent with conditional routing for comprehensive testing."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class RoutingState(TypedDict):
    query: str
    category: str
    documents: list[str]
    response: str


def classifier(state: RoutingState) -> dict:
    """Classify query into a category."""
    query = state["query"].lower()
    if "technical" in query:
        return {"category": "technical"}
    elif "general" in query:
        return {"category": "general"}
    return {"category": "unknown"}


def technical_handler(state: RoutingState) -> dict:
    """Handle technical queries."""
    return {
        "documents": ["tech_doc_1", "tech_doc_2"],
        "response": f"Technical answer for: {state['query']}",
    }


def general_handler(state: RoutingState) -> dict:
    """Handle general queries."""
    return {
        "documents": ["general_doc_1"],
        "response": f"General answer for: {state['query']}",
    }


def fallback_handler(state: RoutingState) -> dict:
    """Handle unknown queries."""
    return {
        "documents": [],
        "response": f"I don't understand: {state['query']}",
    }


def route_by_category(state: RoutingState) -> str:
    """Route to the appropriate handler based on category."""
    category = state.get("category", "unknown")
    if category == "technical":
        return "technical_handler"
    elif category == "general":
        return "general_handler"
    return "fallback_handler"


def create_routing_agent():
    """Create a compiled routing agent with conditional edges."""
    builder = StateGraph(RoutingState)

    builder.add_node("classifier", classifier)
    builder.add_node("technical_handler", technical_handler)
    builder.add_node("general_handler", general_handler)
    builder.add_node("fallback_handler", fallback_handler)

    builder.add_edge(START, "classifier")
    builder.add_conditional_edges("classifier", route_by_category)
    builder.add_edge("technical_handler", END)
    builder.add_edge("general_handler", END)
    builder.add_edge("fallback_handler", END)

    return builder.compile()
