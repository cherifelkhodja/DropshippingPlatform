"""Database Configuration.

Provides async SQLAlchemy engine and session factory for PostgreSQL.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.app.infrastructure.db.models.base import Base


class DatabaseConfig:
    """Configuration for database connection.

    Attributes:
        url: PostgreSQL connection URL (asyncpg driver).
        echo: Whether to log SQL statements.
        pool_size: Connection pool size.
        max_overflow: Maximum overflow connections.
    """

    def __init__(
        self,
        url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        """Initialize database configuration.

        Args:
            url: PostgreSQL connection URL (must use asyncpg driver).
            echo: Whether to log SQL statements.
            pool_size: Connection pool size.
            max_overflow: Maximum overflow connections.
        """
        self.url = url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow


class Database:
    """Async database manager.

    Manages the SQLAlchemy async engine and session factory.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize database manager.

        Args:
            config: Database configuration.
        """
        self._config = config
        self._engine: AsyncEngine = create_async_engine(
            config.url,
            echo=config.echo,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get the async engine."""
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory."""
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new database session.

        Yields:
            AsyncSession: A new database session.

        Example:
            async with database.session() as session:
                result = await session.execute(query)
        """
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_all(self) -> None:
        """Create all tables in the database.

        Should only be used for testing or initial setup.
        For production, use Alembic migrations.
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self) -> None:
        """Drop all tables in the database.

        WARNING: This is destructive. Use only for testing.
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        """Close the database engine and cleanup connections."""
        await self._engine.dispose()
