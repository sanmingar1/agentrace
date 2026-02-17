"""Tests for the simple test agent."""

from tests.agents.simple_agent import create_simple_agent


def test_simple_agent_runs():
    agent = create_simple_agent()
    result = agent.invoke({"query": "test query"})

    assert result["query"] == "test query"
    assert len(result["documents"]) == 3
    assert len(result["processed"]) == 3
    assert result["response"].startswith("Generated answer:")


def test_simple_agent_documents_match_query():
    agent = create_simple_agent()
    result = agent.invoke({"query": "agentrace"})

    for doc in result["documents"]:
        assert "agentrace" in doc


def test_simple_agent_processor_uppercases():
    agent = create_simple_agent()
    result = agent.invoke({"query": "hello"})

    for processed_doc in result["processed"]:
        assert processed_doc == processed_doc.upper()
