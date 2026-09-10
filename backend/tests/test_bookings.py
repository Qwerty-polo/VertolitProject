import pytest

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from unittest.mock import patch

KYIV_TZ = ZoneInfo("Europe/Kyiv")


def future_datetime(hours_from_now: int = 24) -> str:
    value = datetime.now(KYIV_TZ) + timedelta(hours=hours_from_now)

    return value.replace(
        minute=0,
        second=0,
        microsecond=0,
    ).isoformat()


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

    starts_at_value = future_datetime()

    booking_payload = {
        "service_id": service_id,
        "customer_name": "Ivan",
        "customer_phone": "+380991112233",
        "starts_at": starts_at_value,
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
        starts_at_value
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
        "starts_at": future_datetime(),
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
        "starts_at": future_datetime(),
        "guests": 4,
        "duration_hours": 2,
        "comment": "Too short",
    }

    response = await client.post(
        "/api/v1/bookings/",
        json=booking_payload,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Minimum booking duration is 3 hours"
    )


@pytest.mark.asyncio
async def test_overlapping_pending_bookings_are_allowed(client):
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

    first_start = future_datetime(24)
    second_start = future_datetime(25)

    first_booking = {
        "service_id": service_id,
        "customer_name": "Ivan",
        "customer_phone": "+380991112233",
        "starts_at": first_start,
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
        "starts_at": second_start,
        "guests": 3,
        "duration_hours": 3,
        "comment": "Conflict booking",
    }

    response = await client.post(
        "/api/v1/bookings/",
        json=conflicting_booking,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


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
        "starts_at": future_datetime(),
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


@pytest.mark.asyncio
async def test_get_all_bookings(client):
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
        "starts_at": future_datetime(),
        "guests": 4,
        "duration_hours": 3,
        "comment": "Test booking",
    }

    create_response = await client.post(
        "/api/v1/bookings/",
        json=booking_payload,
    )

    assert create_response.status_code == 201

    response = await client.get(
        "/api/v1/bookings/"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    assert any(
        booking["customer_name"] == "Ivan"
        and booking["service_id"] == service_id
        for booking in data
    )


@pytest.mark.asyncio
async def test_get_booking_by_id(client):
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
        "starts_at": future_datetime(),
        "guests": 4,
        "duration_hours": 3,
        "comment": "Test booking",
    }

    create_response = await client.post(
        "/api/v1/bookings/",
        json=booking_payload,
    )

    booking_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/bookings/{booking_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == booking_id
    assert data["customer_name"] == "Ivan"
    assert data["service_id"] == service_id


@pytest.mark.asyncio
async def test_get_booking_not_found(client):
    response = await client.get(
        "/api/v1/bookings/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


@pytest.mark.asyncio
async def test_update_booking_status(client):
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
        "starts_at": future_datetime(),
        "guests": 4,
        "duration_hours": 3,
        "comment": "Test booking",
    }

    create_response = await client.post(
        "/api/v1/bookings/",
        json=booking_payload,
    )

    booking_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == booking_id
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_update_booking_status_not_found(client):
    response = await client.patch(
        "/api/v1/bookings/999999/status",
        json={"status": "cancelled"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


@pytest.mark.asyncio
async def test_booking_guests_must_be_positive(client):
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
        "/api/v1/bookings/",
        json={
            "service_id": service_id,
            "customer_name": "Ivan",
            "customer_phone": "+380991112233",
            "starts_at": future_datetime(),
            "guests": 0,
            "duration_hours": 3,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_booking_duration_must_be_positive(client):
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
        "/api/v1/bookings/",
        json={
            "service_id": service_id,
            "customer_name": "Ivan",
            "customer_phone": "+380991112233",
            "starts_at": future_datetime(),
            "guests": 4,
            "duration_hours": 0,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_booking_cannot_start_in_past(client):
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

    past_time = datetime.now(timezone.utc) - timedelta(hours=1)

    response = await client.post(
        "/api/v1/bookings/",
        json={
            "service_id": service_id,
            "customer_name": "Ivan",
            "customer_phone": "+380991112233",
            "starts_at": past_time.isoformat(),
            "guests": 4,
            "duration_hours": 3,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cannot_confirm_overlapping_booking(client):
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

    first_start = future_datetime(24)
    second_start = future_datetime(25)

    first_response = await client.post(
        "/api/v1/bookings/",
        json={
            "service_id": service_id,
            "customer_name": "Ivan",
            "customer_phone": "+380991112233",
            "starts_at": first_start,
            "guests": 4,
            "duration_hours": 3,
        },
    )

    second_response = await client.post(
        "/api/v1/bookings/",
        json={
            "service_id": service_id,
            "customer_name": "Petro",
            "customer_phone": "+380992223344",
            "starts_at": second_start,
            "guests": 2,
            "duration_hours": 3,
        },
    )

    first_booking_id = first_response.json()["id"]
    second_booking_id = second_response.json()["id"]

    confirm_first = await client.patch(
        f"/api/v1/bookings/{first_booking_id}/status",
        json={"status": "confirmed"},
    )

    assert confirm_first.status_code == 200
    assert confirm_first.json()["status"] == "confirmed"

    confirm_second = await client.patch(
        f"/api/v1/bookings/{second_booking_id}/status",
        json={"status": "confirmed"},
    )

    assert confirm_second.status_code == 409
    assert (
        confirm_second.json()["detail"]
        == "This time slot is already confirmed"
    )


@pytest.mark.asyncio
async def test_create_booking_sends_celery_notification(client):
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
    starts_at = future_datetime()

    with patch(
        "app.api.v1.bookings.send_booking_notification.delay"
    ) as delay_mock:
        response = await client.post(
            "/api/v1/bookings/",
            json={
                "service_id": service_id,
                "customer_name": "Ivan",
                "customer_phone": "+380991112233",
                "starts_at": starts_at,
                "guests": 4,
                "duration_hours": 3,
                "comment": "Test booking",
            },
        )

    assert response.status_code == 201

    data = response.json()

    delay_mock.assert_called_once()

    called_args = delay_mock.call_args.args

    assert called_args[0] == data["id"]
    assert called_args[1] == service_id

    celery_starts_at = datetime.fromisoformat(
        called_args[2].replace("Z", "+00:00")
    )

    response_starts_at = datetime.fromisoformat(
        data["starts_at"].replace("Z", "+00:00")
    )

    assert celery_starts_at == response_starts_at