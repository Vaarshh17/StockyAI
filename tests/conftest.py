"""
tests/conftest.py — Shared pytest fixtures.
"""
import pytest
import pytest_asyncio
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def seeded_db():
    """Set up a fresh in-memory test DB with seed data."""
    import os
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    from db.models import init_db
    await init_db()
    from db.seed import seed_demo_data
    await seed_demo_data()
    yield
    # cleanup handled by garbage collection for in-memory DB

@pytest_asyncio.fixture
async def mock_db():
    """Minimal DB setup without seed data."""
    import os
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    from db.models import init_db
    await init_db()
    yield
