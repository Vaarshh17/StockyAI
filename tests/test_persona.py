"""
tests/unit/test_persona.py — Unit tests for agent/persona.py
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestOnboardingFlow:
    @pytest.mark.asyncio
    async def test_full_onboarding(self, reset_persona):
        from agent.persona import start_onboarding, process_onboarding_answer, is_onboarded, get_persona
        start_onboarding(1)

        # Step 1: Name
        reply, complete = await process_onboarding_answer(1, "Ahmad")
        assert not complete
        assert "language" in reply.lower() or "🌐" in reply

        # Step 2: Language
        reply, complete = await process_onboarding_answer(1, "Malay")
        assert not complete
        assert "commodit" in reply.lower() or "📦" in reply

        # Step 3: Commodities
        reply, complete = await process_onboarding_answer(1, "tomato, bayam, cili")
        assert not complete
        assert "city" in reply.lower() or "🌤️" in reply

        # Step 4: City — completes onboarding
        with patch("db.queries.db_save_persona", new=AsyncMock()):
            reply, complete = await process_onboarding_answer(1, "Kuala Lumpur")
        assert complete
        assert "Ahmad" in reply

        # Verify persona is stored
        persona = get_persona(1)
        assert persona["name"] == "Ahmad"
        assert persona["language"] == "Bahasa Malaysia"
        assert "tomato" in persona["commodities"]
        assert persona["city"] == "Kuala Lumpur"

    def test_is_onboarded_false_initially(self, reset_persona):
        from agent.persona import is_onboarded
        assert is_onboarded(999) is False

    def test_is_onboarded_true_after_complete(self, reset_persona):
        from agent.persona import _personas, is_onboarded
        _personas[1] = {"name": "Test", "language": "English", "commodities": [], "city": "KL"}
        assert is_onboarded(1) is True

    def test_get_onboarding_step_none_initially(self, reset_persona):
        from agent.persona import get_onboarding_step
        assert get_onboarding_step(999) is None

    def test_start_onboarding_sets_step(self, reset_persona):
        from agent.persona import start_onboarding, get_onboarding_step
        start_onboarding(1)
        assert get_onboarding_step(1) == "name"


class TestLanguageMap:
    @pytest.mark.asyncio
    async def test_bahasa_maps_to_bahasa_malaysia(self, reset_persona):
        from agent.persona import start_onboarding, process_onboarding_answer, _personas
        start_onboarding(2)
        await process_onboarding_answer(2, "Test")
        await process_onboarding_answer(2, "Bahasa")
        assert _personas[2]["language"] == "Bahasa Malaysia"

    @pytest.mark.asyncio
    async def test_chinese_maps_to_mandarin(self, reset_persona):
        from agent.persona import start_onboarding, process_onboarding_answer, _personas
        start_onboarding(3)
        await process_onboarding_answer(3, "Test")
        await process_onboarding_answer(3, "中文")
        assert _personas[3]["language"] == "Mandarin"


class TestLoadPersona:
    @pytest.mark.asyncio
    async def test_load_from_db_caches(self, reset_persona):
        from agent.persona import load_persona, _personas
        with patch("db.queries.db_get_persona", new=AsyncMock(return_value={"name": "DB User", "language": "English", "commodities": [], "city": "KL"})):
            result = await load_persona(5)
        assert result["name"] == "DB User"
        assert 5 in _personas

    @pytest.mark.asyncio
    async def test_returns_cached_without_db_call(self, reset_persona):
        from agent.persona import load_persona, _personas
        _personas[6] = {"name": "Cached", "language": "English"}
        with patch("db.queries.db_get_persona", new=AsyncMock()) as mock_db:
            result = await load_persona(6)
            mock_db.assert_not_called()
        assert result["name"] == "Cached"


class TestBuildProfileBlock:
    def test_includes_all_fields(self, reset_persona):
        from agent.persona import build_profile_block
        persona = {"name": "Ahmad", "language": "Bahasa Malaysia", "commodities": ["tomato", "cili"], "city": "KL"}
        block = build_profile_block(persona)
        assert "Ahmad" in block
        assert "tomato" in block
        assert "KL" in block

    def test_empty_commodities(self, reset_persona):
        from agent.persona import build_profile_block
        persona = {"name": "Test", "language": "English", "commodities": [], "city": "KL"}
        block = build_profile_block(persona)
        assert "not specified" in block
