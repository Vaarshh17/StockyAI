"""
tests/integration/test_bot.py — Integration tests for Telegram bot handlers.
Uses python-telegram-bot's fake update/context utilities.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


def make_update(text: str = None, user_id: int = 12345, voice: bool = False, forwarded: bool = False):
    """Build a minimal telegram.Update for testing handlers."""
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.full_name = "Test User"

    message = MagicMock()
    message.text = text
    message.chat = MagicMock()
    message.chat.send_action = AsyncMock()

    if voice:
        voice_obj = MagicMock()
        voice_obj.get_file = AsyncMock(return_value=MagicMock(download_as_bytearray=AsyncMock(return_value=bytearray(b"fake ogg"))))
        message.voice = voice_obj
        message.text = None
    else:
        message.voice = None

    if forwarded:
        origin = MagicMock()
        origin.sender_user_name = "Pak Ali"
        origin.sender_user = None
        origin.date = datetime.now()
        message.forward_origin = origin
        message.text = text or "Forwarded message"
    else:
        message.forward_origin = None

    update.message = message
    return update


def make_context(args=None):
    """Build a minimal ContextTypes.DEFAULT_TYPE."""
    context = MagicMock()
    context.args = args or []
    return context


class TestHandleStart:
    @pytest.mark.asyncio
    async def test_start_clears_history_and_adds_user(self, reset_memory, reset_persona):
        from bot.handlers import handle_start, ACTIVE_USERS
        update = make_update("/start", user_id=42)

        with patch("bot.handlers.load_persona", new=AsyncMock(return_value=None)):
            with patch("bot.handlers.is_onboarded", return_value=False):
                await handle_start(update, make_context())

        assert 42 in ACTIVE_USERS
        update.message.reply_text.assert_called_once()
        called_text = update.message.reply_text.call_args[0][0]
        assert "Stocky AI" in called_text

    @pytest.mark.asyncio
    async def test_start_onboarded_user_gets_welcome_back(self, reset_memory, reset_persona):
        from bot.handlers import handle_start
        from agent.persona import _personas
        _personas[42] = {"name": "Ahmad", "language": "English", "commodities": [], "city": "KL"}

        update = make_update("/start", user_id=42)

        with patch("bot.handlers.load_persona", new=AsyncMock(return_value={"name": "Ahmad"})):
            with patch("bot.handlers.is_onboarded", return_value=True):
                with patch("bot.handlers.get_persona", return_value={"name": "Ahmad"}):
                    await handle_start(update, make_context())

        called_text = update.message.reply_text.call_args[0][0]
        assert "Welcome back" in called_text or "Ahmad" in called_text


class TestHandleMessage:
    @pytest.mark.asyncio
    async def test_onboarding_gate(self, reset_memory, reset_persona):
        from bot.handlers import handle_message
        from agent.persona import _onboarding
        _onboarding[42] = "name"

        update = make_update("Ahmad", user_id=42)

        with patch("bot.handlers.process_onboarding_answer", new=AsyncMock(return_value=("Next question", False))):
            await handle_message(update, make_context())

        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_text_message_routes_to_agent(self, reset_memory, reset_persona):
        from bot.handlers import handle_message

        update = make_update("berapa stok tomato?", user_id=42)

        with patch("bot.handlers.is_onboarded", return_value=True):
            with patch("bot.handlers.get_onboarding_step", return_value=None):
                with patch("bot.handlers.run_agent", new=AsyncMock(return_value={"text": "Stok tomato: 800kg", "needs_approval": False, "draft_id": None})):
                    await handle_message(update, make_context())

        update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_voice_message_transcribed(self, reset_memory, reset_persona):
        from bot.handlers import handle_message

        update = make_update(user_id=42, voice=True)

        with patch("bot.handlers.is_onboarded", return_value=True):
            with patch("bot.handlers.get_onboarding_step", return_value=None):
                with patch("bot.handlers.transcribe_voice", new=AsyncMock(return_value="stok tomato berapa")):
                    with patch("bot.handlers.run_agent", new=AsyncMock(return_value={"text": "800kg", "needs_approval": False, "draft_id": None})):
                        await handle_message(update, make_context())

        # Should have called reply_text at least once (echo + response)
        assert update.message.reply_text.call_count >= 1

    @pytest.mark.asyncio
    async def test_voice_transcription_failure(self, reset_memory, reset_persona):
        from bot.handlers import handle_message

        update = make_update(user_id=42, voice=True)

        with patch("bot.handlers.is_onboarded", return_value=True):
            with patch("bot.handlers.get_onboarding_step", return_value=None):
                with patch("bot.handlers.transcribe_voice", new=AsyncMock(return_value="")):
                    await handle_message(update, make_context())

        called_text = update.message.reply_text.call_args[0][0]
        assert "Maaf" in called_text or "tidak dapat" in called_text

    @pytest.mark.asyncio
    async def test_forwarded_message(self, reset_memory, reset_persona):
        from bot.handlers import handle_message

        update = make_update("tomato RM2.50", user_id=42, forwarded=True)

        with patch("bot.handlers.is_onboarded", return_value=True):
            with patch("bot.handlers.get_onboarding_step", return_value=None):
                with patch("bot.handlers.run_agent", new=AsyncMock(return_value={"text": "Noted", "needs_approval": False, "draft_id": None})) as mock_agent:
                    await handle_message(update, make_context())
                    call_kwargs = mock_agent.call_args[1]
                    assert call_kwargs["input_type"] == "forwarded"


class TestHandleCallback:
    @pytest.mark.asyncio
    async def test_approve_callback(self, reset_memory, reset_persona):
        from bot.handlers import handle_callback
        from agent.memory import save_draft

        save_draft(42, "abc123", {"recipient": "Pak Ali", "message": "Test message"})

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "approve_abc123"
        update.callback_query.from_user.id = 42
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        with patch("bot.handlers.get_draft", return_value={"recipient": "Pak Ali", "message": "Test message"}):
            await handle_callback(update, make_context())

        update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_callback(self, reset_memory, reset_persona):
        from bot.handlers import handle_callback

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "edit_abc123"
        update.callback_query.from_user.id = 42
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        await handle_callback(update, make_context())
        update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_missing_draft(self, reset_memory, reset_persona):
        from bot.handlers import handle_callback

        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "approve_nonexistent"
        update.callback_query.from_user.id = 42
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        with patch("bot.handlers.get_draft", return_value=None):
            await handle_callback(update, make_context())

        called_text = update.callback_query.edit_message_text.call_args[0][0]
        assert "tidak dijumpai" in called_text


class TestHandleCommandTrigger:
    @pytest.mark.asyncio
    async def test_trigger_morning_brief(self, reset_memory, reset_persona):
        from bot.handlers import handle_command_trigger

        update = make_update("/trigger_brief morning", user_id=42)
        context = make_context(args=["morning"])

        with patch("bot.handlers.run_proactive_brief", new=AsyncMock(return_value="Morning brief output")):
            await handle_command_trigger(update, context)

        update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_trigger_default_is_morning(self, reset_memory, reset_persona):
        from bot.handlers import handle_command_trigger

        update = make_update("/trigger_brief", user_id=42)
        context = make_context(args=[])

        with patch("bot.handlers.run_proactive_brief", new=AsyncMock(return_value="Brief")) as mock:
            await handle_command_trigger(update, context)
            mock.assert_called_once_with(42, "morning")


class TestSendResponse:
    @pytest.mark.asyncio
    async def test_normal_response(self):
        from bot.handlers import _send_response
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        await _send_response(update, {"text": "Hello", "needs_approval": False, "draft_id": None})
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_draft_response_with_keyboard(self):
        from bot.handlers import _send_response
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        await _send_response(update, {"text": "Draft msg", "needs_approval": True, "draft_id": "abc"})
        update.message.reply_text.assert_called_once()
        call_kwargs = update.message.reply_text.call_args[1]
        assert "reply_markup" in call_kwargs
