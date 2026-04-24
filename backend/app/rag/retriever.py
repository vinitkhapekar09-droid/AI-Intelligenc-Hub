# rag/retriever.py
#
# WHY THIS FILE EXISTS:
# vector_store.py handles raw storage operations.
# This file sits above it and formats results specifically
# for use by the chat agent — filtering low-quality matches,
# formatting context strings, and returning source attribution.

from .embedder import embed_text
from .vector_store import search


# WHY 0.3 as minimum score?
# Cosine similarity below 0.3 means the chunk is not meaningfully
# related to the query. Including irrelevant chunks confuses the LLM
# and produces worse answers.
MINIMUM_RELEVANCE_SCORE = 0.3


def retrieve(
    query: str,
    n_results: int = 5,
    doc_type: str = None,
    issue_date: str | None = None,
) -> dict:
    """
    Retrieves the most relevant chunks for a given query.

    Returns a dict with:
    - context: formatted string to inject into LLM prompt
    - sources: list of source attributions for the response
    - chunks_found: how many relevant chunks were found

    WHY return a dict instead of raw chunks?
    The chat agent needs context (for the prompt) and sources
    (for attribution in the response) — bundling them together
    makes the chat agent code cleaner.
    """
    query_embedding = embed_text(query)
    raw_results = search(
        query_embedding,
        n_results=n_results,
        doc_type=doc_type,
        issue_date=issue_date,
    )

    # Filter out low-relevance results
    relevant = [r for r in raw_results if r["score"] >= MINIMUM_RELEVANCE_SCORE]

    if not relevant:
        return {
            "context": "",
            "sources": [],
            "chunks_found": 0,
        }

    # Build context string — this gets injected into the LLM prompt
    # WHY number the chunks? It helps the LLM reference them clearly.
    context_parts = []
    for i, chunk in enumerate(relevant, 1):
        meta = chunk["metadata"]
        context_parts.append(
            f"[{i}] Source: {meta['source']} | Type: {meta['doc_type']} | Issue Date: {meta.get('issue_date', 'unknown')}\n"
            f"Title: {meta['title']}\n"
            f"{chunk['text']}\n"
        )
    context = "\n---\n".join(context_parts)

    # Build sources list for attribution in chat responses
    sources = []
    seen_urls = set()  # Deduplicate sources by URL
    for chunk in relevant:
        meta = chunk["metadata"]
        url = meta.get("url", "")
        if url and url not in seen_urls:
            sources.append(
                {
                    "title": meta["title"],
                    "source": meta["source"],
                    "url": url,
                    "doc_type": meta["doc_type"],
                    "issue_date": meta.get("issue_date"),
                }
            )
            seen_urls.add(url)

    return {
        "context": context,
        "sources": sources,
        "chunks_found": len(relevant),
    }
