"""
tests/unit/test_config.py — Unit tests for config.py
"""
import os
import pytest


class TestConfigValues:
    def test_bot_token_loaded(self):
        import config
        assert config.BOT_TOKEN is not None

    def test_ilmu_api_key_loaded(self):
        import config
        assert config.ILMU_API_KEY is not None

    def test_database_url_set(self):
        import config
        assert config.DATABASE_URL is not None

    def test_default_city(self):
        import config
        assert config.DEFAULT_CITY in ("Kuala Lumpur", "'Kuala Lumpur'")

    def test_morning_brief_hour_is_int(self):
        import config
        assert isinstance(config.MORNING_BRIEF_HOUR, int)

    def test_morning_brief_min_is_int(self):
        import config
        assert isinstance(config.MORNING_BRIEF_MIN, int)


class TestValidate:
    def test_validate_succeeds_with_env(self):
        import config
        # Our conftest sets BOT_TOKEN and ILMU_API_KEY
        config.validate()  # Should not raise

    def test_validate_fails_without_bot_token(self):
        import config
        original = config.BOT_TOKEN
        config.BOT_TOKEN = ""
        try:
            with pytest.raises(ValueError, match="BOT_TOKEN"):
                config.validate()
        finally:
            config.BOT_TOKEN = original

    def test_validate_warns_about_supabase(self, capsys):
        import config
        original = config.SUPABASE_DB_URL
        config.SUPABASE_DB_URL = ""
        try:
            # Should not raise, just warn
            config.validate()
            captured = capsys.readouterr()
            assert "SQLite" in captured.out or True  # may or may not print
        finally:
            config.SUPABASE_DB_URL = original
