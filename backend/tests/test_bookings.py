import pytest
from datetime import datetime

@pytest.mark.asyncio
async def test_create_booking(client):
    service_payload = {
        "name": "Sauna",
        "description": "Test sauna",
        "price": 1500,
        "minimum_duration_hours": 3,
    }

    service_response = await client.post(
        "/api/v1/services/",
        json=service_payload,
    )

    service_id = service_response.json()["id"]

    booking_payload = {
        "service_id": service_id,
        "customer_name": "Ivan",
        "customer_phone": "+380991112233",
        "starts_at": "2026-09-10T13:00:00+03:00",
        "guests": 4,
        "duration_hours": 3,
        "comment": "Test booking",
    }
    response = await client.post(
        "/api/v1/bookings/",
        json=booking_payload,
    )
    assert response.status_code == 201
    data = response.json()

    starts_at = datetime.fromisoformat(
        data["starts_at"].replace("Z", "+00:00")
    )

    ends_at = datetime.fromisoformat(
        data["ends_at"].replace("Z", "+00:00")
    )
    expected_starts_at = datetime.fromisoformat(
        "2026-09-10T13:00:00+03:00"
    )

    assert starts_at == expected_starts_at
    assert (ends_at - starts_at).total_seconds() == 3 * 3600

    assert data["service_id"] == service_id
    assert data["customer_name"] == "Ivan"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_booking_service_not_found(client):
    booking_payload = {
        "service_id": 999999,
        "customer_name": "Ivan",
        "customer_phone": "+380991112233",
        "starts_at": "2026-09-10T13:00:00+03:00",
        "guests": 4,
        "duration_hours": 3,
        "comment": "Test booking",
    }

    response = await client.post(
        "/api/v1/bookings/",
        json=booking_payload,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


@pytest.mark.asyncio
async def test_create_booking_duration_too_short(client):
    service_payload = {
        "name": "Sauna",
        "description": "Test sauna",
        "price": 1500,
        "minimum_duration_hours": 3,
    }

    service_response = await client.post(
        "/api/v1/services/",
        json=service_payload,
    )

    service_id = service_response.json()["id"]

    booking_payload = {
        "service_id": service_id,
        "customer_name": "Ivan",
        "customer_phone": "+380991112233",
        "starts_at": "2026-09-10T13:00:00+03:00",
        "guests": 4,
        "duration_hours": 2,
        "comment": "Too short",
    }

    response = await client.post(
        "/api/v1/bookings/",
        json=booking_payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Minimum booking duration is 3 hours"


@pytest.mark.asyncio
async def test_create_booking_conflict(client):
    service_payload = {
        "name": "Sauna",
        "description": "Test sauna",
        "price": 1500,
        "minimum_duration_hours": 3,
    }

    service_response = await client.post(
        "/api/v1/services/",
        json=service_payload,
    )

    service_id = service_response.json()["id"]

    first_booking = {
        "service_id": service_id,
        "customer_name": "Ivan",
        "customer_phone": "+380991112233",
        "starts_at": "2026-09-10T13:00:00+03:00",
        "guests": 4,
        "duration_hours": 3,
        "comment": "First booking",
    }

    first_response = await client.post(
        "/api/v1/bookings/",
        json=first_booking,
    )

    assert first_response.status_code == 201

    conflicting_booking = {
        "service_id": service_id,
        "customer_name": "Petro",
        "customer_phone": "+380991112244",
        "starts_at": "2026-09-10T14:00:00+03:00",
        "guests": 3,
        "duration_hours": 3,
        "comment": "Conflict booking",
    }

    response = await client.post(
        "/api/v1/bookings/",
        json=conflicting_booking,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "This time slot is already booked"


@pytest.mark.asyncio
async def test_cancelled_booking_does_not_block_slot(client):
    service_payload = {
        "name": "Sauna",
        "description": "Test sauna",
        "price": 1500,
        "minimum_duration_hours": 3,
    }

    service_response = await client.post(
        "/api/v1/services/",
        json=service_payload,
    )

    service_id = service_response.json()["id"]

    booking_payload = {
        "service_id": service_id,
        "customer_name": "Ivan",
        "customer_phone": "+380991112233",
        "starts_at": "2026-09-10T13:00:00+03:00",
        "guests": 4,
        "duration_hours": 3,
        "comment": "First booking",
    }

    first_response = await client.post(
        "/api/v1/bookings/",
        json=booking_payload,
    )

    assert first_response.status_code == 201

    booking_id = first_response.json()["id"]

    cancel_response = await client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "cancelled"},
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    second_response = await client.post(
        "/api/v1/bookings/",
        json=booking_payload,
    )

    assert second_response.status_code == 201