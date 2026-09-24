"""One-shot entry point for running the daily digest outside Celery.

Intended for a scheduled ECS/Fargate task. It reuses the same pipeline as
EC2's Celery worker and exits when the pipeline finishes.
"""

from app.services.digest_pipeline import run_daily_digest_pipeline


def main() -> None:
    result = run_daily_digest_pipeline()
    print(f"[digest-job] Pipeline result: {result}")

    if result.get("status") not in {"done", "aborted"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
