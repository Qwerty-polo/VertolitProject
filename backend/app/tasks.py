import logging

from app.celery_app import celery_app


logger = logging.getLogger("vertolit.tasks")


@celery_app.task(
    name="send_booking_notification",
)
def send_booking_notification(
    booking_id: int,
    service_id: int,
    starts_at: str,
):
    logger.info(
        "New booking notification: "
        "booking_id=%s service_id=%s starts_at=%s",
        booking_id,
        service_id,
        starts_at,
    )

    return {
        "status": "sent",
        "booking_id": booking_id,
    }