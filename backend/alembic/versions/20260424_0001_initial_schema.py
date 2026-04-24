"""Initial application schema.

Revision ID: 20260424_0001
Revises:
Create Date: 2026-04-24 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260424_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_issues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="published"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_daily_issues_id"), "daily_issues", ["id"], unique=False)
    op.create_index(
        op.f("ix_daily_issues_issue_date"),
        "daily_issues",
        ["issue_date"],
        unique=True,
    )

    op.create_table(
        "subscribers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("subscribed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subscribers_email"), "subscribers", ["email"], unique=True)
    op.create_index(op.f("ix_subscribers_id"), "subscribers", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "content_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("doc_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("doc_type", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["daily_issues.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doc_id"),
    )
    op.create_index(op.f("ix_content_items_doc_id"), "content_items", ["doc_id"], unique=True)
    op.create_index(op.f("ix_content_items_doc_type"), "content_items", ["doc_type"], unique=False)
    op.create_index(op.f("ix_content_items_id"), "content_items", ["id"], unique=False)
    op.create_index(op.f("ix_content_items_issue_date"), "content_items", ["issue_date"], unique=False)
    op.create_index(op.f("ix_content_items_issue_id"), "content_items", ["issue_id"], unique=False)
    op.create_index(op.f("ix_content_items_published_at"), "content_items", ["published_at"], unique=False)

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("doc_type", sa.String(), nullable=True),
        sa.Column("sources_used", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("thread_id", sa.String(), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_created_at"), "conversations", ["created_at"], unique=False)
    op.create_index(op.f("ix_conversations_id"), "conversations", ["id"], unique=False)
    op.create_index(op.f("ix_conversations_thread_id"), "conversations", ["thread_id"], unique=False)
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_thread_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_created_at"), table_name="conversations")
    op.drop_table("conversations")

    op.drop_index(op.f("ix_content_items_published_at"), table_name="content_items")
    op.drop_index(op.f("ix_content_items_issue_id"), table_name="content_items")
    op.drop_index(op.f("ix_content_items_issue_date"), table_name="content_items")
    op.drop_index(op.f("ix_content_items_id"), table_name="content_items")
    op.drop_index(op.f("ix_content_items_doc_type"), table_name="content_items")
    op.drop_index(op.f("ix_content_items_doc_id"), table_name="content_items")
    op.drop_table("content_items")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_subscribers_id"), table_name="subscribers")
    op.drop_index(op.f("ix_subscribers_email"), table_name="subscribers")
    op.drop_table("subscribers")

    op.drop_index(op.f("ix_daily_issues_issue_date"), table_name="daily_issues")
    op.drop_index(op.f("ix_daily_issues_id"), table_name="daily_issues")
    op.drop_table("daily_issues")
