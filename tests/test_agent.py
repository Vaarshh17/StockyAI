"""
tests/test_agent.py — Tests for the agent loop (mocks GLM API).
"""
import pytest
import json
from unittest.mock import AsyncMock, patch


MOCK_INVENTORY = [
    {"commodity": "tomato", "quantity_kg": 800, "days_remaining": 3, "entry_date": "2024-04-18"}
]


@pytest.mark.asyncio
async def test_agent_calls_get_inventory_for_stock_question():
    tool_call_response = {
        "content": None,
        "tool_calls": [{
            "id": "call_1",
            "type": "function",
            "function": {"name": "get_inventory", "arguments": "{}"}
        }]
    }
    final_response = {
        "content": "Stok tomato semasa: 800kg.",
        "tool_calls": None
    }

    with patch("agent.core.call_llm", new=AsyncMock(side_effect=[tool_call_response, final_response])):
        with patch("agent.core.execute_tool", new=AsyncMock(return_value=MOCK_INVENTORY)):
            with patch("agent.core.get_persona", return_value=None):
                with patch("agent.core.load_persona", new=AsyncMock(return_value=None)):
                    from agent.core import run_agent
                    result = await run_agent(user_id=999, input_text="Berapa stok tomato?")
    assert "tomato" in result["text"].lower() or "800" in result["text"]
    assert result["needs_approval"] is False


@pytest.mark.asyncio
async def test_agent_draft_requires_approval():
    mock_response = {
        "content": "DRAFT_MESSAGE::Pak Ali::malay::Pak Ali, boleh sedia 2 tan tomato Khamis?",
        "tool_calls": None
    }
    with patch("agent.core.call_llm", new=AsyncMock(return_value=mock_response)):
        with patch("agent.core.get_persona", return_value=None):
            with patch("agent.core.load_persona", new=AsyncMock(return_value=None)):
                from agent.core import run_agent
                result = await run_agent(
                    user_id=999,
                    input_text="Draftkan mesej untuk Pak Ali, nak 2 tan tomato Khamis"
                )
    assert result["needs_approval"] is True
    assert result["draft_id"] is not None


@pytest.mark.asyncio
async def test_agent_handles_max_iterations():
    always_tool_call = {
        "content": None,
        "tool_calls": [{
            "id": "call_x",
            "type": "function",
            "function": {"name": "get_inventory", "arguments": "{}"}
        }]
    }
    with patch("agent.core.call_llm", new=AsyncMock(return_value=always_tool_call)):
        with patch("agent.core.execute_tool", new=AsyncMock(return_value=[])):
            with patch("agent.core.get_persona", return_value=None):
                with patch("agent.core.load_persona", new=AsyncMock(return_value=None)):
                    from agent.core import run_agent
                    result = await run_agent(user_id=999, input_text="test")
    assert "text" in result
