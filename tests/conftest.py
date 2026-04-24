"""
tests/conftest.py — Shared pytest fixtures.
"""
import os
import pytest
import pytest_asyncio

# Force in-memory SQLite for all tests BEFORE any module imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DEMO_MODE"] = "True"
os.environ["ILMU_API_KEY"] = "sk-test-fake-key-12345"
os.environ["BOT_TOKEN"] = "0000000000:FAKE_TOKEN_FOR_TESTS"


@pytest_asyncio.fixture
async def fresh_db():
    """Fresh in-memory DB with schema but no data."""
    from db.models import init_db, engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def seeded_db():
    """In-memory DB with full seed data."""
    from db.models import init_db
    await init_db()
    from db.seed import seed_demo_data
    await seed_demo_data()
    yield


@pytest.fixture
def mock_glm():
    """Patch services.glm.call_llm to return configurable responses."""
    from unittest.mock import AsyncMock, patch
    with patch("services.glm.call_llm", new=AsyncMock()) as mock:
        yield mock


@pytest.fixture
def mock_call_llm():
    """Patch agent.core.call_llm."""
    from unittest.mock import AsyncMock, patch
    with patch("agent.core.call_llm", new=AsyncMock()) as mock:
        yield mock


@pytest.fixture
def mock_execute_tool():
    """Patch agent.tools.execute_tool."""
    from unittest.mock import AsyncMock, patch
    with patch("agent.tools.execute_tool", new=AsyncMock()) as mock:
        yield mock


@pytest.fixture
def reset_memory():
    """Clear in-memory stores between tests."""
    from agent.memory import _history, _drafts
    _history.clear()
    _drafts.clear()
    yield
    _history.clear()
    _drafts.clear()


@pytest.fixture
def reset_persona():
    """Clear persona cache between tests."""
    from agent.persona import _personas, _onboarding
    _personas.clear()
    _onboarding.clear()
    yield
    _personas.clear()
    _onboarding.clear()
