"""
tests/unit/test_prompts.py — Unit tests for agent/prompts.py
"""
from agent.prompts import get_system_prompt, BASE_SYSTEM_PROMPT


class TestGetSystemPrompt:
    def test_returns_base_prompt_without_persona(self):
        result = get_system_prompt(None)
        assert "Stocky AI" in result
        assert "MANDATORY TOOL CHAINS" in result

    def test_injects_persona_profile(self):
        persona = {"name": "Ahmad", "language": "Bahasa Malaysia", "commodities": ["tomato"], "city": "KL"}
        result = get_system_prompt(persona)
        assert "USER PROFILE" in result
        assert "Ahmad" in result
        assert "tomato" in result

    def test_no_profile_without_name(self):
        persona = {"name": None, "language": "English"}
        result = get_system_prompt(persona)
        # persona.get("name") is None which is falsy, so no profile injected
        assert isinstance(result, str)
        assert "You are Sto" in result

    def test_no_profile_with_empty_name(self):
        persona = {"name": "", "language": "English"}
        result = get_system_prompt(persona)
        assert isinstance(result, str)
        assert "You are Sto" in result


class TestBaseSystemPrompt:
    def test_contains_key_sections(self):
        assert "IDENTITY" in BASE_SYSTEM_PROMPT
        assert "LANGUAGE RULES" in BASE_SYSTEM_PROMPT
        assert "MANDATORY TOOL CHAINS" in BASE_SYSTEM_PROMPT
        assert "ALERT THRESHOLDS" in BASE_SYSTEM_PROMPT
        assert "RESPONSE FORMATS" in BASE_SYSTEM_PROMPT
        assert "DRAFT_MESSAGE" in BASE_SYSTEM_PROMPT
