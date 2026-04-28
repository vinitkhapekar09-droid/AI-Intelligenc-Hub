from celery import Celery
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
