"""
tests/unit/test_glm.py — Unit tests for services/glm.py
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.glm import call_llm, _mock_response, _get_client


class TestMockResponse:
    def test_returns_demo_mode_message(self):
        messages = [{"role": "user", "content": "test message here"}]
        result = _mock_response(messages)
        assert "DEMO MODE" in result["content"]
        assert result["tool_calls"] is None

    def test_echoes_input_content(self):
        messages = [{"role": "user", "content": "berapa stok tomato?"}]
        result = _mock_response(messages)
        assert "berapa stok" in result["content"]


class TestCallLlm:
    @pytest.mark.asyncio
    async def test_demo_mode_returns_mock(self):
        with patch("config.DEMO_MODE", True):
            result = await call_llm([{"role": "user", "content": "test"}])
        assert result["content"] is not None
        assert result["tool_calls"] is None

    @pytest.mark.asyncio
    async def test_live_mode_calls_openai(self):
        mock_msg = MagicMock()
        mock_msg.content = "Hello from ILMU"
        mock_msg.tool_calls = None

        mock_choice = MagicMock()
        mock_choice.message = mock_msg

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("config.DEMO_MODE", False):
            with patch("services.glm._get_client", return_value=mock_client):
                result = await call_llm([{"role": "user", "content": "hello"}])

        assert result["content"] == "Hello from ILMU"
        assert result["tool_calls"] is None

    @pytest.mark.asyncio
    async def test_live_mode_with_tool_calls(self):
        tc = MagicMock()
        tc.id = "call_1"
        tc.function.name = "get_inventory"
        tc.function.arguments = "{}"

        mock_msg = MagicMock()
        mock_msg.content = None
        mock_msg.tool_calls = [tc]

        mock_choice = MagicMock()
        mock_choice.message = mock_msg

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("config.DEMO_MODE", False):
            with patch("services.glm._get_client", return_value=mock_client):
                result = await call_llm([{"role": "user", "content": "stok?"}], tools=[{"type": "function", "function": {"name": "get_inventory"}}])

        assert result["tool_calls"] is not None
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "get_inventory"

    @pytest.mark.asyncio
    async def test_fast_model_uses_model_fast(self):
        mock_client = AsyncMock()
        mock_msg = MagicMock()
        mock_msg.content = "fast"
        mock_msg.tool_calls = None
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("config.DEMO_MODE", False):
            with patch("services.glm._get_client", return_value=mock_client):
                with patch("config.MODEL_FAST", "ilmu-nemo-nano"):
                    await call_llm([{"role": "user", "content": "test"}], use_fast_model=True)
                    call_kwargs = mock_client.chat.completions.create.call_args[1]
                    assert call_kwargs["model"] == "ilmu-nemo-nano"


class TestGetClient:
    def test_lazy_init(self):
        import services.glm as glm_mod
        glm_mod._client = None
        with patch("config.ILMU_API_KEY", "sk-test-key"):
            with patch("config.ILMU_API_URL", "https://api.ilmu.ai/v1"):
                client = _get_client()
                assert client is not None
                glm_mod._client = None  # cleanup
