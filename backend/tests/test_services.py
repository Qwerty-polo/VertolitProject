import pytest

pytestmark = pytest.mark.usefixtures(
    "admin_auth_override"
)

@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"



@pytest.mark.asyncio
async def test_create_service(client):
    payload = {
        "name": "Sauna",
        "description": "Test sauna",
        "price": 1500,
        "minimum_duration_hours": 3,
    }

    response = await client.post(
        "/api/v1/services/",
        json=payload,
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert data["name"] == "Sauna"
    assert data["description"] == "Test sauna"
    assert data["price"] == 1500
    assert data["minimum_duration_hours"] == 3
    assert "id" in data


@pytest.mark.asyncio
async def test_get_all_services(client):
    payload = {
        "name": "Sauna",
        "description": "Test sauna",
        "price": 1500,
        "minimum_duration_hours": 3,
    }

    create_response = await client.post(
        "/api/v1/services/",
        json=payload,
    )

    assert create_response.status_code in (200, 201)

    response = await client.get("/api/v1/services/")

    assert response.status_code == 200

    data = response.json()

    assert any(
        service["name"] == "Sauna"
        and service["price"] == 1500
        and service["minimum_duration_hours"] == 3
        for service in data
    )