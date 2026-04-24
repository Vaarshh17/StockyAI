"""
tests/conftest.py — Shared pytest fixtures.

Key design: we must force SQLite for tests. The problem is that config.py
calls load_dotenv(override=True), which overwrites os.environ values we set
here. So we patch config module attributes directly, then rebuild the engine.

Critical: SQLite in-memory DBs are connection-local. Each new connection
gets a fresh empty DB. We use StaticPool to share ONE connection so that
tables created by create_all are visible to all sessions.
"""
import pytest
import pytest_asyncio
from sqlalchemy.pool import StaticPool


# ── Step 1: Patch config module attributes BEFORE any db import ────────────
# This must happen at conftest load time (before test collection).
import config
config.SUPABASE_DB_URL = ""
config.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
config.DEMO_MODE = True
config.ILMU_API_KEY = "sk-test-fake-key-12345"
config.BOT_TOKEN = "0000000000:FAKE_TOKEN_FOR_TESTS"

# ── Step 2: Rebuild the engine with SQLite + StaticPool ────────────────────
# StaticPool keeps a single connection alive so all sessions share the same
# in-memory database. Without this, each AsyncSessionLocal() call opens a
# new connection that sees no tables.
from db.models import _make_engine, Base, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

_test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
_TestSessionFactory = sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


# ── Step 3: Monkey-patch db.models to use the test engine/factory ──────────
import db.models as _models
_models.engine = _test_engine
_models.AsyncSessionLocal = _TestSessionFactory

# Also patch db.queries so every `AsyncSessionLocal()` gets the test factory
import db.queries as _queries
_queries.AsyncSessionLocal = _TestSessionFactory


# ── Step 4: Create schema once at session start ────────────────────────────
# Because StaticPool shares one connection, create_all only needs to run
# once. Individual fixtures can clear data between tests.
@pytest_asyncio.fixture(loop_scope="session")
async def _setup_schema():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def fresh_db(_setup_schema):
    """Fresh in-memory DB with schema. Truncates all data between tests."""
    async with _test_engine.begin() as conn:
        # Delete all rows from all tables (keep schema)
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest_asyncio.fixture
async def seeded_db(_setup_schema):
    """In-memory DB with full seed data."""
    # Clear existing data first
    async with _test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
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


# ── Auto-mark async tests for strict asyncio_mode ──────────────────────────
def pytest_collection_modifyitems(items):
    """Automatically add @pytest.mark.asyncio to all async test functions."""
    for item in items:
        if isinstance(item, pytest.Function) and item.obj is not None:
            import asyncio
            if asyncio.iscoroutinefunction(item.obj):
                item.add_marker(pytest.mark.asyncio)
