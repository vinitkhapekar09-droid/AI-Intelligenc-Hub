"""Celery entry point retained for the current EC2 deployment."""

from ..core.celery_app import celery_app
from ..services.digest_pipeline import run_daily_digest_pipeline


@celery_app.task(name="app.tasks.digest_tasks.run_daily_digest")
def run_daily_digest():
    """Delegate to the standalone digest pipeline."""
    task_id = getattr(run_daily_digest.request, "id", None)
    return run_daily_digest_pipeline(task_id=task_id)
