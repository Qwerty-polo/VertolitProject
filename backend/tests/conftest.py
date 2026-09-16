from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models
from app.config import settings
from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.security.admin_auth import require_admin

test_engine = create_async_engine(
    settings.test_database_url,
    echo=False,
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with test_session_maker() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def admin_auth_override():
    async def fake_require_admin():
        return "test-admin-token"

    app.dependency_overrides[require_admin] = fake_require_admin

    yield

    app.dependency_overrides.pop(
        require_admin,
        None,
    )


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with test_engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))

        await connection.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def mock_redis():
    with (
        patch(
            "app.api.v1.services.redis_client.get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.api.v1.services.redis_client.set",
            new_callable=AsyncMock,
        ),
        patch(
            "app.cache.redis_client.delete",
            new_callable=AsyncMock,
        ),
        patch(
            "app.middleware.rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "app.middleware.rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ),
        patch(
            "app.security.booking_rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "app.security.booking_rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ),
        patch(
            "app.security.admin_login_rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "app.security.admin_login_rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ),
    ):
        yield


@pytest.fixture
def test_db_session_maker():
    return test_session_maker
