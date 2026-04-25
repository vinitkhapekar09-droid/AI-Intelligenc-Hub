# rag/embedder.py
#
# WHY THIS FILE EXISTS:
# This module generates embeddings for document chunks and user queries.
# We intentionally use a hosted embedding API instead of a local model so the
# RAG pipeline is easier to deploy and much lighter on memory.

import hashlib
from math import sqrt

from google import genai
from google.genai import types

from ..core.config import settings
from .chunker import TextChunk

_client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY.strip() else None
_PLACEHOLDER_KEYS = {"your_key", "test", "demo", "changeme", "change-me"}


def _normalize_vector(values: list[float]) -> list[float]:
    magnitude = sqrt(sum(value * value for value in values))
    if magnitude == 0:
        return values
    return [value / magnitude for value in values]


def _use_demo_embeddings() -> bool:
    api_key = settings.GEMINI_API_KEY.strip().lower()
    if not api_key:
        return True
    return api_key in _PLACEHOLDER_KEYS or api_key.startswith("your_")


def _tokenize(text: str) -> list[str]:
    return [token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if token]


def _demo_embed(text: str) -> list[float]:
    dimensions = settings.EMBEDDING_DIMENSIONS
    vector = [0.0] * dimensions
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    return _normalize_vector(vector)


def _embed_many(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    if _use_demo_embeddings() or _client is None:
        return [_demo_embed(text) for text in texts]

    try:
        response = _client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="SEMANTIC_SIMILARITY",
                output_dimensionality=settings.EMBEDDING_DIMENSIONS,
            ),
        )
        return [_normalize_vector(list(item.values)) for item in response.embeddings]
    except Exception as exc:
        print(f"[embedder] Falling back to demo embeddings: {exc}")
        return [_demo_embed(text) for text in texts]


def embed_text(text: str) -> list[float]:
    embeddings = _embed_many([text])
    return embeddings[0] if embeddings else []


def embed_chunks(chunks: list[TextChunk]) -> list[dict]:
    if not chunks:
        return []

    print(f"[embedder] Embedding {len(chunks)} chunks with {settings.EMBEDDING_MODEL}...")
    vectors = _embed_many([chunk.text for chunk in chunks])

    embedded = []
    for chunk, vector in zip(chunks, vectors):
        embedded.append(
            {
                "id": chunk.chunk_id,
                "embedding": vector,
                "text": chunk.text,
                "metadata": {
                    "doc_id": chunk.doc_id,
                    "doc_type": chunk.doc_type,
                    "source": chunk.source,
                    "title": chunk.title,
                    "url": chunk.url,
                    "issue_date": chunk.timestamp[:10] if chunk.timestamp else "",
                },
            }
        )

    print(
        f"[embedder] Done. Vector dimension: "
        f"{len(embedded[0]['embedding']) if embedded else 0}"
    )
    return embedded
