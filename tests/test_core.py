"""
tests/unit/test_core.py — Unit tests for agent/core.py (agent loop)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestRunAgent:
    @pytest.mark.asyncio
    async def test_simple_response_no_tools(self, mock_call_llm, reset_memory, reset_persona):
        mock_call_llm.return_value = {
            "content": "Stok tomato ada 800kg.",
            "tool_calls": None,
        }
        with patch("agent.core.get_persona", return_value=None):
            from agent.core import run_agent
            result = await run_agent(user_id=1, input_text="berapa stok tomato?")
        assert result["text"] == "Stok tomato ada 800kg."
        assert result["needs_approval"] is False
        assert result["draft_id"] is None

    @pytest.mark.asyncio
    async def test_tool_call_then_final_response(self, mock_call_llm, reset_memory, reset_persona):
        tool_call_response = {
            "content": None,
            "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "get_inventory", "arguments": "{}"}
            }],
        }
        final_response = {
            "content": "Stok tomato: 800kg.",
            "tool_calls": None,
        }
        mock_call_llm.side_effect = [tool_call_response, final_response]

        with patch("agent.core.execute_tool", new=AsyncMock(return_value=[{"commodity": "tomato", "quantity_kg": 800}])):
            with patch("agent.core.get_persona", return_value=None):
                from agent.core import run_agent
                result = await run_agent(user_id=1, input_text="stok tomato?")
        assert "tomato" in result["text"].lower() or "800" in result["text"]

    @pytest.mark.asyncio
    async def test_draft_message_detection(self, mock_call_llm, reset_memory, reset_persona):
        mock_call_llm.return_value = {
            "content": "DRAFT_MESSAGE::Pak Ali::malay::Pak Ali, boleh sedia 2 tan tomato Khamis?",
            "tool_calls": None,
        }
        with patch("agent.core.get_persona", return_value=None):
            from agent.core import run_agent
            result = await run_agent(user_id=1, input_text="draft mesej untuk Pak Ali")
        assert result["needs_approval"] is True
        assert result["draft_id"] is not None

    @pytest.mark.asyncio
    async def test_max_tool_iterations(self, mock_call_llm, reset_memory, reset_persona):
        always_tool_call = {
            "content": None,
            "tool_calls": [{
                "id": "call_x",
                "type": "function",
                "function": {"name": "get_inventory", "arguments": "{}"}
            }],
        }
        mock_call_llm.return_value = always_tool_call

        with patch("agent.core.execute_tool", new=AsyncMock(return_value=[])):
            with patch("agent.core.get_persona", return_value=None):
                from agent.core import run_agent
                result = await run_agent(user_id=1, input_text="test")
        assert "text" in result

    @pytest.mark.asyncio
    async def test_forwarded_message_formatting(self, mock_call_llm, reset_memory, reset_persona):
        mock_call_llm.return_value = {
            "content": "Noted.",
            "tool_calls": None,
        }
        with patch("agent.core.get_persona", return_value=None):
            from agent.core import run_agent
            result = await run_agent(
                user_id=1,
                input_forwarded={"original_sender": "Pak Ali", "original_date": "2024-04-20", "text": "tomato RM2.50"},
                input_type="forwarded",
            )
        assert result["text"] == "Noted."

    @pytest.mark.asyncio
    async def test_history_saved_after_response(self, mock_call_llm, reset_memory, reset_persona):
        mock_call_llm.return_value = {
            "content": "Hello!",
            "tool_calls": None,
        }
        with patch("agent.core.get_persona", return_value=None):
            from agent.core import run_agent
            await run_agent(user_id=1, input_text="hi")
        from agent.memory import get_history
        history = get_history(1)
        assert len(history) == 2


class TestRunProactiveBrief:
    @pytest.mark.asyncio
    async def test_morning_brief(self, mock_call_llm, reset_memory, reset_persona):
        mock_call_llm.return_value = {
            "content": "Morning brief content here.",
            "tool_calls": None,
        }
        with patch("agent.core.get_persona", return_value=None):
            with patch("agent.instinct.get_instinct", new=AsyncMock(return_value="Stocky nampak sesuatu: test")):
                from agent.core import run_proactive_brief
                result = await run_proactive_brief(user_id=1, brief_type="morning")
        assert "Morning brief" in result
        assert "Stocky nampak" in result

    @pytest.mark.asyncio
    async def test_spoilage_uses_fast_model(self, mock_call_llm, reset_memory, reset_persona):
        mock_call_llm.return_value = {
            "content": "No spoilage risk.",
            "tool_calls": None,
        }
        with patch("agent.core.get_persona", return_value=None):
            from agent.core import run_proactive_brief
            result = await run_proactive_brief(user_id=1, brief_type="spoilage")
        assert mock_call_llm.called
        _, kwargs = mock_call_llm.call_args
        assert kwargs.get("use_fast_model") is True

    @pytest.mark.asyncio
    async def test_digest_appends_instinct(self, mock_call_llm, reset_memory, reset_persona):
        mock_call_llm.return_value = {
            "content": "Weekly digest content.",
            "tool_calls": None,
        }
        with patch("agent.core.get_persona", return_value=None):
            with patch("agent.instinct.get_instinct", new=AsyncMock(return_value="Stocky nampak sesuatu: pattern found")):
                from agent.core import run_proactive_brief
                result = await run_proactive_brief(user_id=1, brief_type="digest")
        assert "pattern found" in result


class TestHandleDraft:
    def test_parses_draft_message_format(self, reset_memory):
        from agent.core import _handle_draft
        text = "DRAFT_MESSAGE::Pak Ali::malay::Boleh sedia 2 tan tomato?"
        result = _handle_draft(1, text)
        assert result["needs_approval"] is True
        assert "Pak Ali" in result["text"]
        assert result["draft_id"] is not None

    def test_malformed_draft_defaults(self, reset_memory):
        from agent.core import _handle_draft
        text = "DRAFT_MESSAGE::badformat"
        result = _handle_draft(1, text)
        assert result["needs_approval"] is True
