#!/usr/bin/env python
"""Regression tests for the digest summarizer."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_summarizer.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("MLFLOW_TRACKING_URL", "")

from app.services import summarizer


def test_summarize_items_falls_back_when_groq_returns_invalid_json(monkeypatch):
    monkeypatch.setattr(summarizer.settings, "MLFLOW_TRACKING_URL", "")
    monkeypatch.setattr(summarizer, "_call_groq_with_retry", lambda prompt: "[{\"headline\": \"broken\"")

    items = [
        {
            "title": "Example AI article",
            "summary": "This is the original source summary.",
            "source": "Example Source",
            "link": "https://example.com/article",
        }
    ]

    summaries = summarizer.summarize_items(items)

    assert len(summaries) == 1
    assert summaries[0]["headline"] == "Example AI article"
    assert summaries[0]["link"] == "https://example.com/article"
    assert "could not be parsed cleanly" in summaries[0]["why_it_matters"]
