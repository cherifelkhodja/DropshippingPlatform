"""Integration test fixtures and configuration."""

import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import aiohttp
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.app.infrastructure.db.models import Base


# Test database URL (use environment variable or default)
# Check TEST_DATABASE_URL first, then DATABASE_URL for CI compatibility
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://dropshipping:dropshipping@localhost:5432/dropshipping_test",
    ),
)

# Mock server URL
MOCK_SERVER_URL = os.getenv("MOCK_SERVER_URL", "http://localhost:8080")


@pytest_asyncio.fixture(loop_scope="function")
async def test_engine():
    """Create test database engine for each test function.

    Note: Using function scope to avoid pytest-asyncio scope mismatch issues.
    Each test gets its own engine and creates/drops tables.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(loop_scope="function")
async def http_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Create aiohttp client session for tests."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def mock_server_url() -> str:
    """Get mock server URL."""
    return MOCK_SERVER_URL


@pytest.fixture
def unique_id() -> str:
    """Generate a unique ID for test data."""
    return str(uuid4())


class FakeLogger:
    """Fake logger for testing."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, dict]] = []

    def info(self, msg: str, **context) -> None:
        self.messages.append(("info", msg, context))

    def warning(self, msg: str, **context) -> None:
        self.messages.append(("warning", msg, context))

    def error(self, msg: str, **context) -> None:
        self.messages.append(("error", msg, context))

    def debug(self, msg: str, **context) -> None:
        self.messages.append(("debug", msg, context))

    def critical(self, msg: str, **context) -> None:
        self.messages.append(("critical", msg, context))


@pytest.fixture
def fake_logger() -> FakeLogger:
    """Create a fake logger for testing."""
    return FakeLogger()
