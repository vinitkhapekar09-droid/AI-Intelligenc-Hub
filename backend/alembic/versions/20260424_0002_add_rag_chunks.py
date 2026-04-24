"""Add SQL-backed rag chunks table.

Revision ID: 20260424_0002
Revises: 20260424_0001
Create Date: 2026-04-24 00:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260424_0002"
down_revision = "20260424_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rag_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.String(), nullable=False),
        sa.Column("doc_id", sa.String(), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("doc_type", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index(op.f("ix_rag_chunks_chunk_id"), "rag_chunks", ["chunk_id"], unique=True)
    op.create_index(op.f("ix_rag_chunks_doc_id"), "rag_chunks", ["doc_id"], unique=False)
    op.create_index(op.f("ix_rag_chunks_doc_type"), "rag_chunks", ["doc_type"], unique=False)
    op.create_index(op.f("ix_rag_chunks_id"), "rag_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_rag_chunks_issue_date"), "rag_chunks", ["issue_date"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rag_chunks_issue_date"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_id"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_doc_type"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_doc_id"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_chunk_id"), table_name="rag_chunks")
    op.drop_table("rag_chunks")
