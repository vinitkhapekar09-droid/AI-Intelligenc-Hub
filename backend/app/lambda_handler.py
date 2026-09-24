"""AWS Lambda handlers for the FastAPI app and standalone digest task."""

from mangum import Mangum

from app.main import app
from app.services.digest_pipeline import run_daily_digest_pipeline

api_handler = Mangum(app, lifespan="off")


def digest_handler(event, context):
    """Execute one digest pipeline invocation."""
    result = run_daily_digest_pipeline()
    if result.get("status") not in {"done", "aborted"}:
        raise RuntimeError(f"Digest pipeline failed: {result}")
    return result
