#!/usr/bin/env python
"""Regression tests for digest issue storage."""

import os
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_digest_store.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("MLFLOW_TRACKING_URL", "")

from app.core.database import Base, SessionLocal, engine
from app.models.content_item import ContentItem
from app.pipeline.normalizer import UnifiedDocument
from app.services.digest_store import store_daily_issue


def _make_document(doc_id: str, title: str, url: str) -> UnifiedDocument:
    return UnifiedDocument(
        title=title,
        content=f"Summary for {title}",
        source="TechCrunch AI",
        doc_type="news",
        url=url,
        timestamp="2026-08-04T00:00:00Z",
        doc_id=doc_id,
    )


def test_store_daily_issue_skips_duplicate_doc_ids(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        db.query(ContentItem).delete()
        db.commit()

        issue_date = date(2026, 8, 4)
        documents = [
            _make_document("duplicate-id", "First item", "https://example.com/1"),
            _make_document("duplicate-id", "Second item", "https://example.com/2"),
        ]
        summaries = [
            {
                "link": "https://example.com/1",
                "simple_summary": "First summary",
                "why_it_matters": "First reason",
            },
            {
                "link": "https://example.com/2",
                "simple_summary": "Second summary",
                "why_it_matters": "Second reason",
            },
        ]

        issue = store_daily_issue(db, issue_date, documents, summaries)

        assert len(issue["items"]) == 1
        assert issue["items"][0]["doc_id"] == "duplicate-id"
        assert issue["items"][0]["summary"] == "First summary"
        assert "1 important AI items" in issue["summary"]
    finally:
        db.close()
