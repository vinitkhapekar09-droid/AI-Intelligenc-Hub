"""AWS Lambda handlers for the API and standalone digest pipeline."""

from mangum import Mangum

from app.main import app
from app.services.digest_pipeline import run_daily_digest_pipeline

# Keep FastAPI lifespan hooks disabled: production schema changes are managed
# through migrations rather than create_all during Lambda initialization.
api_handler = Mangum(app, lifespan="off")


def digest_handler(event, context):
    """Execute the existing digest pipeline once in a Lambda invocation."""
    event = event if isinstance(event, dict) else {}
    result = run_daily_digest_pipeline(task_id=event.get("task_id"))
    if result.get("status") not in {"done", "aborted"}:
        raise RuntimeError(f"Digest pipeline did not complete: {result}")
    return result
