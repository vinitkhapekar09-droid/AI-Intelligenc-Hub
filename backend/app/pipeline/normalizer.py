# pipeline/normalizer.py
#
# WHY THIS FILE EXISTS:
# Our fetcher returns raw dicts from two different sources (arXiv, NewsAPI).
# Each source has slightly different field names and formats.
# This file defines a single, strict schema (UnifiedDocument) that ALL data
# must conform to before entering the RAG pipeline or being used by agents.
# This is the "contract" between the data layer and the intelligence layer.

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class UnifiedDocument:
    """
    A single normalized document from any source.
    Every piece of content in the system — news or research — becomes this.
    """

    title: str  # Clean title, no newlines
    content: str  # Main text content (summary or description)
    source: str  # e.g. "arXiv", "TechCrunch", "NewsAPI"
    doc_type: Literal["news", "research"]  # Tells agents how to handle it
    url: str  # Original link for attribution
    timestamp: str  # ISO format string, e.g. "2024-01-15T10:30:00Z"
    doc_id: str = field(default="")  # Unique ID, auto-generated if not provided

    def __post_init__(self):
        # Auto-generate a simple doc_id from source + title if not given.
        # WHY: Chroma needs a unique ID for every document it stores.
        if not self.doc_id:
            base = f"{self.source}_{self.title[:50]}"
            # Remove characters that could cause issues in vector DBs
            self.doc_id = base.replace(" ", "_").replace("/", "-").lower()


def normalize_arxiv(raw: dict) -> UnifiedDocument:
    """
    Converts a raw arXiv dict (from fetcher.py) into a UnifiedDocument.
    """
    return UnifiedDocument(
        title=raw.get("title", "Untitled"),
        content=raw.get("summary", ""),
        source=raw.get("source", "arXiv"),
        doc_type="research",  # arXiv items are always research papers
        url=raw.get("link", ""),
        timestamp=raw.get("published", datetime.utcnow().isoformat()),
    )


def normalize_news(raw: dict) -> UnifiedDocument:
    """
    Converts a raw NewsAPI dict (from fetcher.py) into a UnifiedDocument.
    """
    return UnifiedDocument(
        title=raw.get("title", "Untitled"),
        content=raw.get("summary", ""),
        source=raw.get("source", "NewsAPI"),
        doc_type="news",  # NewsAPI items are always news
        url=raw.get("link", ""),
        timestamp=raw.get("published", datetime.utcnow().isoformat()),
    )


def normalize_all(raw_items: list[dict]) -> list[UnifiedDocument]:
    """
    Takes the combined raw list from fetch_all_items() and normalizes everything.
    Detects source type by checking the 'source' field.

    WHY: We want one single function that the Celery task can call —
    it doesn't need to know about arXiv vs news internally.
    """
    normalized = []
    for item in raw_items:
        source = item.get("source", "").lower()
        try:
            if source == "arxiv":
                doc = normalize_arxiv(item)
            else:
                doc = normalize_news(item)
            normalized.append(doc)
        except Exception as e:
            # Never crash the whole pipeline because one item is malformed
            print(f"[normalizer] Skipping malformed item: {e}")
            continue

    print(f"[normalizer] Normalized {len(normalized)} documents")
    return normalized
