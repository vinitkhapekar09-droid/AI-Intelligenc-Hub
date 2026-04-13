# rag/embedder.py
#
# WHY THIS FILE EXISTS:
# Before storing chunks in the vector DB, each chunk must be converted
# into a numerical vector (embedding) that captures its semantic meaning.
# We use a lightweight local model so we don't need any API key,
# and it runs fast even on CPU.

from sentence_transformers import SentenceTransformer
from .chunker import TextChunk

# WHY module-level initialization:
# Loading the model takes ~2 seconds. If we loaded it inside the function,
# every single chunk would pay that cost. Loading once at module level
# means we pay it once per worker process.
#
# The model downloads automatically on first use (~80MB, cached after that).
_model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str) -> list[float]:
    """
    Converts a single string into an embedding vector.
    Used for both storing chunks AND embedding user queries at search time.

    WHY list[float]?
    Chroma expects plain Python lists, not numpy arrays.
    .tolist() handles that conversion.
    """
    vector = _model.encode(text, convert_to_numpy=True)
    return vector.tolist()


def embed_chunks(chunks: list[TextChunk]) -> list[dict]:
    """
    Takes a list of TextChunks and returns a list of dicts ready
    to be inserted into Chroma.

    Each dict contains:
    - id: unique chunk ID (Chroma requires this)
    - embedding: the vector
    - text: raw text (stored as Chroma document)
    - metadata: everything else we want to filter/retrieve later

    WHY batch encoding?
    _model.encode() can process a list of texts in one GPU/CPU pass,
    which is significantly faster than encoding one by one.
    """
    if not chunks:
        return []

    print(f"[embedder] Embedding {len(chunks)} chunks...")

    # Batch encode all chunk texts at once for efficiency
    texts = [chunk.text for chunk in chunks]
    vectors = _model.encode(texts, convert_to_numpy=True)

    embedded = []
    for chunk, vector in zip(chunks, vectors):
        embedded.append(
            {
                "id": chunk.chunk_id,
                "embedding": vector.tolist(),
                "text": chunk.text,
                "metadata": {
                    "doc_id": chunk.doc_id,
                    "doc_type": chunk.doc_type,
                    "source": chunk.source,
                    "title": chunk.title,
                    "url": chunk.url,
                },
            }
        )

    print(f"[embedder] Done. Vector dimension: {len(embedded[0]['embedding'])}")
    return embedded
