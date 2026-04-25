"""Add task run tracking table.

Revision ID: 20260424_0003
Revises: 20260424_0002
Create Date: 2026-04-24 01:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260424_0003"
down_revision = "20260424_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("issue_date", sa.String(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_runs_created_at"), "task_runs", ["created_at"], unique=False)
    op.create_index(op.f("ix_task_runs_id"), "task_runs", ["id"], unique=False)
    op.create_index(op.f("ix_task_runs_issue_date"), "task_runs", ["issue_date"], unique=False)
    op.create_index(op.f("ix_task_runs_status"), "task_runs", ["status"], unique=False)
    op.create_index(op.f("ix_task_runs_task_id"), "task_runs", ["task_id"], unique=False)
    op.create_index(op.f("ix_task_runs_task_name"), "task_runs", ["task_name"], unique=False)
    op.create_index(op.f("ix_task_runs_started_at"), "task_runs", ["started_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_runs_started_at"), table_name="task_runs")
    op.drop_index(op.f("ix_task_runs_task_name"), table_name="task_runs")
    op.drop_index(op.f("ix_task_runs_task_id"), table_name="task_runs")
    op.drop_index(op.f("ix_task_runs_status"), table_name="task_runs")
    op.drop_index(op.f("ix_task_runs_issue_date"), table_name="task_runs")
    op.drop_index(op.f("ix_task_runs_id"), table_name="task_runs")
    op.drop_index(op.f("ix_task_runs_created_at"), table_name="task_runs")
    op.drop_table("task_runs")
