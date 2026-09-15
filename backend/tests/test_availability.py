import pytest

import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.usefixtures(
    "admin_auth_override"
)

@pytest.mark.asyncio
async def test_create_availability_block(client):
    service_response = await client.post(
        "/api/v1/services/",
        json={
            "name": "Sauna",
            "description": "Test sauna",
            "price": 1500,
            "minimum_duration_hours": 3,
        },
    )
    service_id = service_response.json()["id"]

    response = await client.post(
        "/api/v1/availability-blocks/",
        json={
            "service_id": service_id,
            "starts_at": "2026-09-20T14:00:00+00:00",
            "ends_at": "2026-09-20T17:00:00+00:00",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["service_id"] == service_id
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_availability_block_service_not_found(client):
    response = await client.post(
        "/api/v1/availability-blocks/",
        json={
            "service_id": 999999,
            "starts_at": "2026-09-20T14:00:00+00:00",
            "ends_at": "2026-09-20T17:00:00+00:00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


@pytest.mark.asyncio
async def test_availability_block_end_must_be_after_start(client):
    response = await client.post(
        "/api/v1/availability-blocks/",
        json={
            "service_id": 1,
            "starts_at": "2026-09-20T17:00:00+00:00",
            "ends_at": "2026-09-20T14:00:00+00:00",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_availability_blocks(client):
    service_response = await client.post(
        "/api/v1/services/",
        json={
            "name": "Sauna",
            "description": "Test sauna",
            "price": 1500,
            "minimum_duration_hours": 3,
        },
    )
    service_id = service_response.json()["id"]

    await client.post(
        "/api/v1/availability-blocks/",
        json={
            "service_id": service_id,
            "starts_at": "2026-09-20T14:00:00+00:00",
            "ends_at": "2026-09-20T17:00:00+00:00",
        },
    )

    response = await client.get(
        "/api/v1/availability-blocks/"
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["service_id"] == service_id


@pytest.mark.asyncio
async def test_availability_excludes_admin_block(client):
    service_response = await client.post(
        "/api/v1/services/",
        json={
            "name": "Sauna",
            "description": "Test sauna",
            "price": 1500,
            "minimum_duration_hours": 3,
        },
    )
    service_id = service_response.json()["id"]

    await client.post(
        "/api/v1/availability-blocks/",
        json={
            "service_id": service_id,
            "starts_at": "2026-09-20T14:00:00+00:00",
            "ends_at": "2026-09-20T17:00:00+00:00",
        },
    )

    response = await client.get(
        f"/api/v1/services/{service_id}/availability",
        params={"date": "2026-09-20"},
    )

    assert response.status_code == 200

    slots = response.json()

    # Ці старти перетинаються з блоком 14:00–17:00
    assert "2026-09-20T12:00:00+00:00" not in slots
    assert "2026-09-20T13:00:00+00:00" not in slots
    assert "2026-09-20T14:00:00+00:00" not in slots
    assert "2026-09-20T15:00:00+00:00" not in slots
    assert "2026-09-20T16:00:00+00:00" not in slots


@pytest.mark.asyncio
async def test_availability_empty_when_whole_day_blocked(client):
    service_response = await client.post(
        "/api/v1/services/",
        json={
            "name": "Sauna",
            "description": "Test sauna",
            "price": 1500,
            "minimum_duration_hours": 3,
        },
    )
    service_id = service_response.json()["id"]

    await client.post(
        "/api/v1/availability-blocks/",
        json={
            "service_id": service_id,
            "starts_at": "2026-09-20T10:00:00+03:00",
            "ends_at": "2026-09-20T22:00:00+03:00",
        },
    )

    response = await client.get(
        f"/api/v1/services/{service_id}/availability",
        params={"date": "2026-09-20"},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_availability_service_not_found(client):
    response = await client.get(
        "/api/v1/services/999999/availability",
        params={"date": "2026-09-20"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


@pytest.mark.asyncio
async def test_availability_uses_kyiv_timezone(client):
    service_response = await client.post(
        "/api/v1/services/",
        json={
            "name": "Sauna",
            "description": "Test sauna",
            "price": 1500,
            "minimum_duration_hours": 3,
        },
    )
    service_id = service_response.json()["id"]

    response = await client.get(
        f"/api/v1/services/{service_id}/availability",
        params={"date": "2026-09-20"},
    )

    assert response.status_code == 200

    slots = response.json()

    assert len(slots) > 0

    # Вересень у Europe/Kyiv має UTC+03:00
    assert slots[0] == "2026-09-20T10:00:00+03:00"


@pytest.mark.asyncio
async def test_availability_returns_cached_slots(client):
    cached_slots = [
        "2026-09-20T10:00:00+03:00",
        "2026-09-20T11:00:00+03:00",
    ]

    service_response = await client.post(
        "/api/v1/services/",
        json={
            "name": "Sauna",
            "description": "Test",
            "price": 1000,
            "minimum_duration_hours": 3,
        },
    )

    service_id = service_response.json()["id"]

    with patch(
        "app.api.v1.services.redis_client.get",
        new_callable=AsyncMock,
        return_value='["2026-09-20T10:00:00+03:00", "2026-09-20T11:00:00+03:00"]',
    ):
        response = await client.get(
            f"/api/v1/services/{service_id}/availability",
            params={"date": "2026-09-20"},
        )

    assert response.status_code == 200
    assert response.json() == cached_slots


@pytest.mark.asyncio
async def test_availability_is_saved_to_cache(client):
    service_response = await client.post(
        "/api/v1/services/",
        json={
            "name": "Sauna",
            "description": "Test",
            "price": 1000,
            "minimum_duration_hours": 3,
        },
    )

    service_id = service_response.json()["id"]

    with (
        patch(
            "app.api.v1.services.redis_client.get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.api.v1.services.redis_client.set",
            new_callable=AsyncMock,
        ) as set_mock,
    ):
        response = await client.get(
            f"/api/v1/services/{service_id}/availability",
            params={"date": "2026-09-20"},
        )

    assert response.status_code == 200
    set_mock.assert_awaited_once()