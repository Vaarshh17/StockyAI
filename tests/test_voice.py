"""
tests/unit/test_voice.py — Unit tests for services/voice.py
"""
import pytest
from unittest.mock import patch, MagicMock
from services.voice import transcribe_voice


class TestTranscribeVoice:
    @pytest.mark.asyncio
    async def test_empty_bytes_returns_empty(self):
        result = await transcribe_voice(b"")
        assert result == ""

    @pytest.mark.asyncio
    async def test_none_bytes_returns_empty(self):
        result = await transcribe_voice(None)
        assert result == ""

    @pytest.mark.asyncio
    async def test_model_failure_returns_empty(self):
        with patch("services.voice._get_model", side_effect=ImportError("no whisper")):
            result = await transcribe_voice(b"fake ogg data")
            assert result == ""

    @pytest.mark.asyncio
    async def test_successful_transcription(self):
        mock_model = MagicMock()
        segment1 = MagicMock()
        segment1.text = "Hello "
        segment2 = MagicMock()
        segment2.text = "world"
        mock_model.transcribe.return_value = (
            [segment1, segment2],
            MagicMock(language="en"),
        )
        with patch("services.voice._get_model", return_value=mock_model):
            result = await transcribe_voice(b"fake ogg data")
        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_language_hint_passed(self):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], MagicMock(language="ms"))
        with patch("services.voice._get_model", return_value=mock_model):
            await transcribe_voice(b"fake ogg", language_hint="ms")
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["language"] == "ms"

    @pytest.mark.asyncio
    async def test_transcription_failure_returns_empty(self):
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception("transcription error")
        with patch("services.voice._get_model", return_value=mock_model):
            result = await transcribe_voice(b"fake ogg data")
        assert result == ""
