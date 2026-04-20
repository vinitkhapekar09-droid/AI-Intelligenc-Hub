# rag/vector_store.py
#
# WHY THIS FILE EXISTS:
# This is the interface between our app and ChromaDB.
# All vector storage and retrieval logic lives here.
# The rest of the app never imports chromadb directly —
# it only calls functions from this file.
# WHY? If we ever swap Chroma for Pinecone or FAISS,
# we only change this one file. Nothing else breaks.

import chromadb
from chromadb.config import Settings as ChromaSettings
from .embedder import embed_text
from ..core.config import settings


# WHY this path?
# /tmp/chroma is writable in Docker containers and Codespaces.
# In production (DigitalOcean), we'll mount a persistent volume here.
CHROMA_PATH = settings.CHROMA_PATH
COLLECTION_NAME = "ai_hub_documents"

# Module-level client — created once, reused across all calls.
# WHY: Creating a new client on every function call would be slow
# and could cause file lock conflicts with ChromaDB's SQLite backend.
_client = chromadb.PersistentClient(
    path=CHROMA_PATH,
    # Don't send usage data
    settings=ChromaSettings(anonymized_telemetry=False),
)


def get_collection():
    """
    Gets or creates the Chroma collection.
    get_or_create means: if collection exists, return it; if not, create it.
    WHY: Safe to call on every app startup without wiping existing data.
    """
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        # cosine similarity for text embeddings
        metadata={"hnsw:space": "cosine"},
    )


def store_chunks(embedded_chunks: list[dict]) -> int:
    """
    Stores embedded chunks into Chroma.

    WHY upsert instead of add?
    upsert = insert if new, update if ID already exists.
    This means running the daily digest twice won't create duplicates.
    """
    if not embedded_chunks:
        return 0

    collection = get_collection()

    ids = [c["id"] for c in embedded_chunks]
    embeddings = [c["embedding"] for c in embedded_chunks]
    documents = [c["text"] for c in embedded_chunks]
    metadatas = [c["metadata"] for c in embedded_chunks]

    # Upsert in batches of 100 to avoid memory issues with large ingestions
    batch_size = 100
    total_stored = 0

    for i in range(0, len(embedded_chunks), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        batch_documents = documents[i:i + batch_size]
        batch_metadatas = metadatas[i:i + batch_size]

        collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_documents,
            metadatas=batch_metadatas,
        )
        total_stored += len(batch_ids)

    print(
        f"[vector_store] Stored {total_stored} chunks. "
        f"Collection total: {collection.count()}"
    )
    return total_stored


def search(query: str, n_results: int = 5, doc_type: str = None) -> list[dict]:
    """
    Searches the vector store for chunks similar to the query.

    Args:
        query: The user's question in plain text
        n_results: How many chunks to return
        doc_type: Optional filter — "news", "research", or None for both

    WHY embed the query here?
    The query must be in the same vector space as the stored chunks.
    We use the same embed_text() function for consistency.
    """
    try:
        collection = get_collection()

        # Don't search an empty collection — Chroma throws an error
        total = collection.count()
        if total == 0:
            print("[vector_store] Collection is empty, nothing to search.")
            return []

        query_embedding = embed_text(query)

        # Build optional metadata filter
        where_filter = {"doc_type": doc_type} if doc_type else None

        results = collection.query(
            query_embeddings=[query_embedding],
            # can't ask for more than exists
            n_results=min(n_results, total),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        # Local/dev environments can lose Chroma index files (e.g., temp dir cleanup).
        # Fail open so API returns a helpful fallback response instead of 500.
        print(f"[vector_store] Search failed, returning no results: {e}")
        return []

    # Reformat into clean list of dicts for the rest of the app
    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append(
            {
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1
                - results["distances"][0][i],  # convert distance to similarity
            }
        )

    return chunks


def get_collection_stats() -> dict:
    """
    Returns basic stats about the vector store.
    Used by the /health and /metrics endpoints.
    """
    try:
        collection = get_collection()
        total_chunks = collection.count()
    except Exception as e:
        print(f"[vector_store] Stats unavailable: {e}")
        total_chunks = 0

    return {
        "total_chunks": total_chunks,
        "collection_name": COLLECTION_NAME,
        "storage_path": CHROMA_PATH,
    }
