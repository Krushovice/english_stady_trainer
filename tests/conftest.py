import os
import uuid

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-32-bytes-minimum-for-hs256")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://english_trainer:change-me@localhost:5432/english_trainer_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


def _admin_database_url(database_url: str) -> str:
    base, _, _ = database_url.rpartition("/")
    return f"{base}/postgres"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _test_database():
    """Create an isolated `..._test` database and the schema in it, once per test run.

    Keeps integration tests off the dev database instead of reusing it and
    risking drop_all wiping real data.
    """
    settings = get_settings()
    db_name = settings.database_url.rsplit("/", 1)[-1]

    admin_engine = create_async_engine(
        _admin_database_url(settings.database_url), isolation_level="AUTOCOMMIT"
    )
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await admin_engine.dispose()

    from app.core.db import engine
    from app.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register and log in a fresh user, returning a bearer-auth header dict."""
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "correcthorsebattery"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def override_ai_provider():
    """Swap the app's real AI provider for a test double for the duration of a test.

    Usage: `override_ai_provider(MockAIProvider(response="..."))`. CLAUDE.md
    forbids automated tests from depending on real AI responses, so any test
    that exercises an AI endpoint must call this.
    """
    from app.integrations.ai.factory import get_ai_provider
    from app.main import app

    def _override(provider):
        app.dependency_overrides[get_ai_provider] = lambda: provider

    yield _override
    app.dependency_overrides.pop(get_ai_provider, None)


@pytest_asyncio.fixture
def override_stt_provider():
    """Swap the app's real STT provider for a test double for the duration of a test.

    Usage: `override_stt_provider(MockSTTProvider(transcript="..."))`. Same
    "never hit a real model in tests" rule as `override_ai_provider`.
    """
    from app.integrations.stt.factory import get_stt_provider
    from app.main import app

    def _override(provider):
        app.dependency_overrides[get_stt_provider] = lambda: provider

    yield _override
    app.dependency_overrides.pop(get_stt_provider, None)


@pytest_asyncio.fixture(scope="session")
async def synced_lesson(_test_database):
    """Load the repo's real authored content once per test run.

    Course API tests read against this instead of hand-built fixture rows,
    so a broken content file fails the test suite the same way it would
    fail a real `sync_content` run.
    """
    from pathlib import Path

    from app.core.db import async_session_factory
    from app.services.content_loader import ContentLoaderService

    content_dir = Path(__file__).resolve().parent.parent / "content"
    async with async_session_factory() as session:
        lessons = await ContentLoaderService(session).sync_directory(content_dir)
    return lessons[0]
