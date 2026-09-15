from unittest.mock import (
    AsyncMock,
    patch,
)

import pytest
from redis.exceptions import RedisError

from app.api.v1.admin import settings
from app.security import admin_auth


TEST_ADMIN_PASSWORD = "test-admin-password"


class FakeAdminRedis:
    def __init__(self):
        self.sessions: dict[str, str] = {}

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
    ):
        self.sessions[key] = value
        return True

    async def exists(self, key: str):
        return int(key in self.sessions)

    async def delete(self, key: str):
        existed = key in self.sessions
        self.sessions.pop(key, None)
        return int(existed)


@pytest.fixture
def fake_admin_redis(monkeypatch):
    fake_redis = FakeAdminRedis()

    monkeypatch.setattr(
        admin_auth,
        "redis_client",
        fake_redis,
    )

    monkeypatch.setattr(
        settings,
        "admin_password",
        TEST_ADMIN_PASSWORD,
    )

    monkeypatch.setattr(
        settings,
        "admin_session_ttl_seconds",
        43200,
    )

    monkeypatch.setattr(
        settings,
        "admin_cookie_secure",
        False,
    )

    monkeypatch.setattr(
        settings,
        "cors_origins",
        "http://localhost:3000",
    )

    return fake_redis


@pytest.mark.asyncio
async def test_admin_login_wrong_password(
    client,
    fake_admin_redis,
):
    response = await client.post(
        "/api/v1/admin/login",
        json={
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid admin password"
    }

    assert fake_admin_redis.sessions == {}


@pytest.mark.asyncio
async def test_admin_login_creates_session_and_cookie(
    client,
    fake_admin_redis,
):
    response = await client.post(
        "/api/v1/admin/login",
        json={
            "password": TEST_ADMIN_PASSWORD,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 43200
    assert data["access_token"]

    token = data["access_token"]

    session_key = (
        f"admin_session:{token}"
    )

    assert (
        session_key
        in fake_admin_redis.sessions
    )

    assert (
        response.cookies.get(
            "vertolit_admin_session"
        )
        == token
    )


@pytest.mark.asyncio
async def test_admin_session_requires_auth(
    client,
    fake_admin_redis,
):
    response = await client.get(
        "/api/v1/admin/session"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Admin authentication required"
    }


@pytest.mark.asyncio
async def test_admin_cookie_authentication(
    client,
    fake_admin_redis,
):
    login_response = await client.post(
        "/api/v1/admin/login",
        json={
            "password": TEST_ADMIN_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    response = await client.get(
        "/api/v1/admin/session"
    )

    assert response.status_code == 200

    assert response.json() == {
        "authenticated": True
    }


@pytest.mark.asyncio
async def test_protected_bookings_require_admin(
    client,
    fake_admin_redis,
):
    response = await client.get(
        "/api/v1/bookings/"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Admin authentication required"
    }


@pytest.mark.asyncio
async def test_admin_cookie_allows_access_to_bookings(
    client,
    fake_admin_redis,
):
    login_response = await client.post(
        "/api/v1/admin/login",
        json={
            "password": TEST_ADMIN_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    response = await client.get(
        "/api/v1/bookings/"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_admin_bearer_token_allows_access(
    client,
    fake_admin_redis,
):
    login_response = await client.post(
        "/api/v1/admin/login",
        json={
            "password": TEST_ADMIN_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()[
        "access_token"
    ]

    # Видаляємо cookie спеціально,
    # щоб перевірити саме Bearer auth.
    client.cookies.clear()

    response = await client.get(
        "/api/v1/bookings/",
        headers={
            "Authorization":
                f"Bearer {token}"
        },
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_logout_invalidates_session(
    client,
    fake_admin_redis,
):
    login_response = await client.post(
        "/api/v1/admin/login",
        json={
            "password": TEST_ADMIN_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()[
        "access_token"
    ]

    session_key = (
        f"admin_session:{token}"
    )

    assert (
        session_key
        in fake_admin_redis.sessions
    )

    logout_response = await client.post(
        "/api/v1/admin/logout",
        headers={
            "Origin":
                "http://localhost:3000",
        },
    )

    assert logout_response.status_code == 204

    assert (
        session_key
        not in fake_admin_redis.sessions
    )

    response = await client.get(
        "/api/v1/admin/session"
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cookie_admin_mutation_rejects_foreign_origin(
    client,
    fake_admin_redis,
):
    login_response = await client.post(
        "/api/v1/admin/login",
        json={
            "password": TEST_ADMIN_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    response = await client.post(
        "/api/v1/admin/logout",
        headers={
            "Origin":
                "https://evil.example",
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Invalid request origin"
    }


@pytest.mark.asyncio
async def test_cookie_admin_mutation_accepts_trusted_origin(
    client,
    fake_admin_redis,
):
    login_response = await client.post(
        "/api/v1/admin/login",
        json={
            "password": TEST_ADMIN_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    response = await client.post(
        "/api/v1/admin/logout",
        headers={
            "Origin":
                "http://localhost:3000",
        },
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_bearer_admin_mutation_does_not_require_origin(
    client,
    fake_admin_redis,
):
    login_response = await client.post(
        "/api/v1/admin/login",
        json={
            "password": TEST_ADMIN_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()[
        "access_token"
    ]

    client.cookies.clear()

    response = await client.post(
        "/api/v1/admin/logout",
        headers={
            "Authorization":
                f"Bearer {token}",
        },
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_auth_fails_closed_when_redis_is_down(
    client,
):
    with patch(
        "app.security.admin_auth."
        "redis_client.exists",
        new_callable=AsyncMock,
        side_effect=RedisError(
            "Redis unavailable"
        ),
    ):
        response = await client.get(
            "/api/v1/admin/session",
            headers={
                "Authorization":
                    "Bearer test-token",
            },
        )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Admin authentication "
            "service unavailable"
        )
    }


@pytest.mark.asyncio
async def test_admin_login_fails_closed_when_rate_limiter_redis_is_down(
    client,
):
    with patch(
        "app.security."
        "admin_login_rate_limit."
        "redis_client.incr",
        new_callable=AsyncMock,
        side_effect=RedisError(
            "Redis unavailable"
        ),
    ):
        response = await client.post(
            "/api/v1/admin/login",
            json={
                "password":
                    TEST_ADMIN_PASSWORD,
            },
        )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Admin authentication "
            "service unavailable"
        )
    }