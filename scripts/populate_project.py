from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.models.content_item import ContentItem
from backend.app.models.daily_issue import DailyIssue
from backend.app.models.rag_chunk import RagChunk
from backend.app.pipeline.normalizer import UnifiedDocument
from backend.app.rag.chunker import chunk_all_documents
from backend.app.rag.embedder import embed_chunks
from backend.app.rag.vector_store import store_chunks
from backend.app.services.digest_store import store_daily_issue
from backend.app.services.fetcher import fetch_all_items
from backend.app.services.summarizer import summarize_items


def _build_demo_documents(issue_date: date, issue_index: int) -> tuple[list[UnifiedDocument], list[dict]]:
    stamp = datetime.combine(issue_date, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    suffix = issue_date.isoformat()

    documents = [
        UnifiedDocument(
            title=f"Efficient Agent Memory for Daily Research Workflows {issue_index + 1}",
            content=(
                "Researchers describe a compact memory design for agentic systems that preserves "
                "the most relevant findings across long research sessions while reducing context bloat. "
                "The method prioritizes recent evidence, keeps durable summaries, and makes follow-up "
                "questions easier to answer from grounded context."
            ),
            source="arXiv",
            doc_type="research",
            url=f"https://example.com/research/agent-memory-{suffix}",
            timestamp=stamp,
            doc_id=f"agent-memory-{suffix}",
        ),
        UnifiedDocument(
            title=f"Multimodal Benchmark Reveals Limits in Fast AI Evaluation {issue_index + 1}",
            content=(
                "A new benchmark tests whether multimodal models can reason consistently across images, "
                "video, and text. Results show that headline scores can hide brittle reasoning and unstable "
                "performance when evaluation tasks become more realistic."
            ),
            source="arXiv",
            doc_type="research",
            url=f"https://example.com/research/multimodal-benchmark-{suffix}",
            timestamp=stamp,
            doc_id=f"multimodal-benchmark-{suffix}",
        ),
        UnifiedDocument(
            title=f"AI Infrastructure Startup Expands GPU Capacity {issue_index + 1}",
            content=(
                "An AI infrastructure company announced new GPU capacity targeted at enterprise model training "
                "and inference. The expansion reflects continued pressure on compute availability as more teams "
                "move from prototype systems toward production deployment."
            ),
            source="TechCrunch",
            doc_type="news",
            url=f"https://example.com/news/gpu-capacity-{suffix}",
            timestamp=stamp,
            doc_id=f"gpu-capacity-{suffix}",
        ),
        UnifiedDocument(
            title=f"Open Models Gain Ground in Enterprise AI Procurement {issue_index + 1}",
            content=(
                "Enterprise buyers are increasingly evaluating open models for internal copilots, search, "
                "and knowledge workflows. Cost control, deployment flexibility, and data governance remain "
                "the main reasons teams are choosing open alternatives."
            ),
            source="The Verge",
            doc_type="news",
            url=f"https://example.com/news/open-models-{suffix}",
            timestamp=stamp,
            doc_id=f"open-models-{suffix}",
        ),
    ]

    summaries = [
        {
            "headline": "Agent memory improves",
            "simple_summary": "This paper proposes a lighter way for AI agents to remember important research context over time without carrying every old detail.",
            "why_it_matters": "It shows how long-running AI assistants can stay grounded and useful while keeping memory costs under control.",
            "link": documents[0].url,
        },
        {
            "headline": "Benchmark exposes weak spots",
            "simple_summary": "Researchers built a tougher benchmark for multimodal AI and found that strong public scores do not always translate to stable reasoning.",
            "why_it_matters": "Teams evaluating AI systems need better tests before trusting model quality in production settings.",
            "link": documents[1].url,
        },
        {
            "headline": "GPU capacity grows",
            "simple_summary": "A startup expanded AI compute capacity to meet demand from organizations deploying larger models.",
            "why_it_matters": "Compute availability remains a practical bottleneck for many AI products and research teams.",
            "link": documents[2].url,
        },
        {
            "headline": "Open models advance",
            "simple_summary": "More enterprises are considering open models as they balance performance, cost, and data control.",
            "why_it_matters": "This trend affects how companies choose vendors and structure AI systems internally.",
            "link": documents[3].url,
        },
    ]
    return documents, summaries


def _populate_demo(days: int, reset: bool) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if reset:
            db.query(RagChunk).delete()
            db.query(ContentItem).delete()
            db.query(DailyIssue).delete()
            db.commit()

        created_issues = []
        today = datetime.now(timezone.utc).date()
        for index in range(days):
            issue_date = today - timedelta(days=index)
            documents, summaries = _build_demo_documents(issue_date, index)
            issue = store_daily_issue(db, issue_date, documents, summaries)
            embedded = embed_chunks(chunk_all_documents(documents))
            for item in embedded:
                item["metadata"]["issue_date"] = issue_date.isoformat()
            stored = store_chunks(embedded)
            created_issues.append((issue["issue_date"], len(documents), stored))
    finally:
        db.close()

    print("Demo population complete:")
    for issue_date, doc_count, chunk_count in created_issues:
        print(f"- {issue_date}: {doc_count} documents, {chunk_count} rag chunks")


def _populate_live(max_items: int) -> None:
    Base.metadata.create_all(bind=engine)
    issue_date = datetime.now(timezone.utc).date()
    raw_items = fetch_all_items(max_total=max_items)
    if not raw_items:
        raise SystemExit("No items fetched. Check API keys or network access.")

    summaries = summarize_items(raw_items)
    if not summaries:
        raise SystemExit("Summarization failed. Check GEMINI_API_KEY.")

    documents = [
        UnifiedDocument(
            title=item["title"],
            content=item["summary"],
            source=item["source"],
            doc_type="research" if item["source"].lower() == "arxiv" else "news",
            url=item["link"],
            timestamp=item.get("published") or datetime.now(timezone.utc).isoformat(),
        )
        for item in raw_items
    ]

    db = SessionLocal()
    try:
        issue = store_daily_issue(db, issue_date, documents, summaries)
    finally:
        db.close()

    embedded = embed_chunks(chunk_all_documents(documents))
    for item in embedded:
        item["metadata"]["issue_date"] = issue_date.isoformat()
    stored = store_chunks(embedded)

    print(
        f"Live population complete for {issue['issue_date']}: "
        f"{len(documents)} documents, {stored} rag chunks"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate the project with demo or live data.")
    parser.add_argument("--mode", choices=["demo", "live"], default="demo")
    parser.add_argument("--days", type=int, default=3, help="Number of demo issue dates to create.")
    parser.add_argument("--max-items", type=int, default=8, help="Maximum live items to fetch.")
    parser.add_argument("--no-reset", action="store_true", help="Do not clear existing demo issue/chunk data first.")
    args = parser.parse_args()

    if args.mode == "demo":
        _populate_demo(days=max(args.days, 1), reset=not args.no_reset)
        return

    _populate_live(max_items=max(args.max_items, 2))


if __name__ == "__main__":
    main()
