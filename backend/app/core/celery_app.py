from celery import Celery
from celery.schedules import crontab
from .config import settings

celery_app = Celery(
    "daily_ai_digest",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.digest_tasks"],
)

celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Schedule the task to run every day at 8 AM IST
celery_app.conf.beat_schedule = {
    "send_daily_digest": {
        "task": "app.tasks.digest_tasks.run_daily_digest",
        "schedule": crontab(hour=8, minute=0),
    },
}
