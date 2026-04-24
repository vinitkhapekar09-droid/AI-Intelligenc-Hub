from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import json

from sqlalchemy.orm import Session

from ..models.task_run import TaskRun


def _serialize_detail(detail: Any) -> str | None:
    if detail is None:
        return None
    if isinstance(detail, str):
        return detail
    return json.dumps(detail, default=str)


def start_task_run(
    db: Session,
    *,
    task_name: str,
    issue_date: str | None = None,
    task_id: str | None = None,
) -> TaskRun:
    task_run = TaskRun(
        task_name=task_name,
        status="running",
        started_at=datetime.now(timezone.utc),
        issue_date=issue_date,
        task_id=task_id,
    )
    db.add(task_run)
    db.commit()
    db.refresh(task_run)
    return task_run


def finish_task_run(
    db: Session,
    task_run_id: int,
    *,
    status: str,
    detail: Any = None,
) -> TaskRun | None:
    task_run = db.query(TaskRun).filter(TaskRun.id == task_run_id).first()
    if task_run is None:
        return None

    task_run.status = status
    task_run.finished_at = datetime.now(timezone.utc)
    task_run.detail = _serialize_detail(detail)
    db.commit()
    db.refresh(task_run)
    return task_run


def get_latest_task_run(db: Session, task_name: str) -> TaskRun | None:
    return (
        db.query(TaskRun)
        .filter(TaskRun.task_name == task_name)
        .order_by(TaskRun.started_at.desc())
        .first()
    )
