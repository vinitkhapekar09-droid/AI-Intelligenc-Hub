# rag/chunker.py
#
# WHY THIS FILE EXISTS:
# Vector databases store and search small pieces of text, not full documents.
# Long documents must be split into chunks before embedding.
# We use overlapping chunks so that sentences at chunk boundaries
# are represented in multiple chunks — preventing information loss.

from dataclasses import dataclass
from ..pipeline.normalizer import UnifiedDocument


@dataclass
class TextChunk:
    """
    A single chunk of text, ready to be embedded and stored in the vector DB.
    It carries metadata so we can trace it back to the original document.
    """

    chunk_id: str  # Unique ID: "{doc_id}_chunk_{index}"
    doc_id: str  # ID of the parent UnifiedDocument
    text: str  # The actual chunk text
    doc_type: str  # "news" or "research" — inherited from parent
    source: str  # e.g. "arXiv", "TechCrunch"
    title: str  # Parent document title — useful for citations
    url: str  # Original URL — for attribution in chat responses


def chunk_document(
    doc: UnifiedDocument,
    chunk_size: int = 300,  # Max words per chunk
    overlap: int = 50,  # Words shared between adjacent chunks
) -> list[TextChunk]:
    """
    Splits a UnifiedDocument into overlapping TextChunks.

    WHY words instead of characters?
    Word-based splitting is more natural — it doesn't cut mid-word,
    and embedding models think in tokens (which are close to words).
    """
    words = doc.content.split()

    # If the document is short enough, don't split it at all
    if len(words) <= chunk_size:
        return [
            TextChunk(
                chunk_id=f"{doc.doc_id}_chunk_0",
                doc_id=doc.doc_id,
                text=doc.content,
                doc_type=doc.doc_type,
                source=doc.source,
                title=doc.title,
                url=doc.url,
            )
        ]

    chunks = []
    start = 0
    index = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        chunks.append(
            TextChunk(
                chunk_id=f"{doc.doc_id}_chunk_{index}",
                doc_id=doc.doc_id,
                text=chunk_text,
                doc_type=doc.doc_type,
                source=doc.source,
                title=doc.title,
                url=doc.url,
            )
        )

        # Move forward by (chunk_size - overlap) so next chunk overlaps
        start += chunk_size - overlap
        index += 1

    return chunks


def chunk_all_documents(
    docs: list[UnifiedDocument],
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[TextChunk]:
    """
    Chunks an entire list of UnifiedDocuments.
    This is the function the Celery task will call.
    """
    all_chunks = []
    for doc in docs:
        chunks = chunk_document(doc, chunk_size, overlap)
        all_chunks.extend(chunks)

    print(f"[chunker] Created {len(all_chunks)} chunks from {len(docs)} documents")
    return all_chunks
