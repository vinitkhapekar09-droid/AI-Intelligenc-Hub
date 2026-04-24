# rag/chunker.py
#
# WHY THIS FILE EXISTS:
# Vector databases store and search small pieces of text, not full documents.
# Long documents must be split into chunks before embedding.
# We use overlapping chunks so that sentences at chunk boundaries
# are represented in multiple chunks — preventing information loss.

import re
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
    timestamp: str  # Original publication timestamp


def chunk_document(
    doc: UnifiedDocument,
    chunk_size: int = 1500,  # Max characters per chunk (~300 words)
    overlap: int = 250,  # Overlapping characters
) -> list[TextChunk]:
    """
    Splits a UnifiedDocument into overlapping TextChunks using sentence boundaries.

    WHY sentences instead of words?
    Splitting blindly by words frequently cuts right through the middle of sentences,
    destroying context. Splitting by sentences preserves complete thoughts.
    """
    text = doc.content.strip()

    # If the document is short enough, don't split it at all
    if len(text) <= chunk_size:
        return [
            TextChunk(
                chunk_id=f"{doc.doc_id}_chunk_0",
                doc_id=doc.doc_id,
                text=text,
                doc_type=doc.doc_type,
                source=doc.source,
                title=doc.title,
                url=doc.url,
                timestamp=doc.timestamp,
            )
        ]

    chunks = []
    current_chunk = []
    current_length = 0
    index = 0

    # Split into sentences (naively by punctuation)
    sentences = re.split(r"(?<=[.!?])\s+", text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_len = len(sentence)

        if current_length + sentence_len > chunk_size and current_length > 0:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.doc_id}_chunk_{index}",
                    doc_id=doc.doc_id,
                    text=chunk_text,
                    doc_type=doc.doc_type,
                    source=doc.source,
                    title=doc.title,
                    url=doc.url,
                    timestamp=doc.timestamp,
                )
            )
            index += 1

            # Calculate overlap for next chunk
            overlap_text = []
            overlap_length = 0
            for s in reversed(current_chunk):
                if overlap_length + len(s) > overlap:
                    break
                overlap_text.insert(0, s)
                overlap_length += len(s) + 1

            current_chunk = overlap_text + [sentence]
            current_length = overlap_length + sentence_len
        else:
            current_chunk.append(sentence)
            current_length += sentence_len + 1

    # Add the final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(
            TextChunk(
                chunk_id=f"{doc.doc_id}_chunk_{index}",
                doc_id=doc.doc_id,
                text=chunk_text,
                doc_type=doc.doc_type,
                source=doc.source,
                title=doc.title,
                url=doc.url,
                timestamp=doc.timestamp,
            )
        )

    return chunks


def chunk_all_documents(
    docs: list[UnifiedDocument],
    chunk_size: int = 1500,
    overlap: int = 250,
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
