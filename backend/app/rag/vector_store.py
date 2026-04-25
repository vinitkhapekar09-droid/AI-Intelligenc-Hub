# rag/vector_store.py
#
# WHY THIS FILE EXISTS:
# This module stores and retrieves RAG chunks. The current implementation keeps
# vectors in SQL so the pipeline is easier to run in low-memory environments
# while still being a real retrieval system.

from datetime import date

from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..models.rag_chunk import RagChunk


def _parse_issue_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _dot_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def _query_chunks(
    db: Session,
    doc_type: str | None = None,
    issue_date: str | None = None,
) -> list[RagChunk]:
    query = db.query(RagChunk)

    parsed_issue_date = _parse_issue_date(issue_date)
    if doc_type:
        query = query.filter(RagChunk.doc_type == doc_type)
    if parsed_issue_date:
        query = query.filter(RagChunk.issue_date == parsed_issue_date)

    return query.order_by(RagChunk.issue_date.desc(), RagChunk.id.asc()).all()


def store_chunks(embedded_chunks: list[dict]) -> int:
    if not embedded_chunks:
        return 0

    db = SessionLocal()
    stored_count = 0
    try:
        for item in embedded_chunks:
            metadata = item["metadata"]
            issue_date = _parse_issue_date(metadata.get("issue_date"))
            if issue_date is None:
                continue

            existing = (
                db.query(RagChunk).filter(RagChunk.chunk_id == item["id"]).first()
            )

            if existing is None:
                existing = RagChunk(chunk_id=item["id"])
                db.add(existing)

            existing.doc_id = metadata["doc_id"]
            existing.issue_date = issue_date
            existing.doc_type = metadata["doc_type"]
            existing.source = metadata["source"]
            existing.title = metadata["title"]
            existing.url = metadata.get("url")
            existing.content = item["text"]
            existing.embedding = item["embedding"]
            stored_count += 1

        db.commit()
    finally:
        db.close()

    print(f"[vector_store] Stored {stored_count} chunks in SQL-backed RAG store.")
    return stored_count


def search(
    query_embedding: list[float],
    n_results: int = 5,
    doc_type: str | None = None,
    issue_date: str | None = None,
) -> list[dict]:
    db = SessionLocal()
    try:
        candidates = _query_chunks(db, doc_type=doc_type, issue_date=issue_date)
        if not candidates:
            return []

        ranked = []
        for chunk in candidates:
            score = _dot_similarity(query_embedding, chunk.embedding or [])
            ranked.append(
                {
                    "text": chunk.content,
                    "metadata": {
                        "doc_id": chunk.doc_id,
                        "doc_type": chunk.doc_type,
                        "source": chunk.source,
                        "title": chunk.title,
                        "url": chunk.url,
                        "issue_date": chunk.issue_date.isoformat(),
                    },
                    "score": score,
                }
            )

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[: max(n_results, 1)]
    finally:
        db.close()


def get_collection_stats(db: Session | None = None) -> dict:
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        total_chunks = db.query(RagChunk).count()
    finally:
        if should_close:
            db.close()

    return {
        "total_chunks": total_chunks,
        "collection_name": "rag_chunks",
        "storage_path": "sql_database",
    }
