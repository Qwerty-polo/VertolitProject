from celery import Celery

from app.config import settings
from celery.schedules import crontab

celery_app = Celery(
    "vertolit",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.timezone,
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "check-upcoming-bookings-every-5-minutes": {
        "task": "app.tasks.check_upcoming_bookings",
        "schedule": crontab(minute="*/5"),
    },
}