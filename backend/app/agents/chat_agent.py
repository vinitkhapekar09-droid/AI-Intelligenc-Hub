# agents/chat_agent.py
#
# WHY THIS FILE EXISTS:
# This is the RAG-based chat agent — the core intelligence of the system.
# It combines retrieved context from our vector store with Groq LLaMA
# to answer user questions grounded in real, ingested AI/ML content.
#
# FLOW: question → retrieve context → build prompt → LLM → answer + sources

from groq import Groq
from ..core.config import settings
from ..rag.retriever import retrieve

# WHY module level?
# Groq client is stateless and thread-safe — safe to initialize once.
# Unlike MLflow, it doesn't make network calls at initialization.
_groq_client = Groq(api_key=settings.GROQ_API_KEY)

# The model we use for chat responses.
# llama-3.1-8b-instant is fast and free on Groq.
# WHY not 70b? 8b is sufficient for RAG — the context does the heavy lifting.
CHAT_MODEL = "llama-3.1-8b-instant"


def _build_prompt(question: str, context: str) -> str:
    """
    Builds the RAG prompt.

    WHY this structure?
    - Clear role definition helps the LLM stay focused
    - Explicit context section prevents hallucination
    - "If the context doesn't contain..." prevents confident wrong answers
    - Asking for concise answers keeps responses readable
    """
    return f"""You are an AI research assistant for an AI/ML intelligence hub.
You help users understand the latest AI news and research papers.

Use ONLY the context below to answer the question.
If the context doesn't contain enough information to answer,
say "I don't have enough information about that in my current knowledge base."
Do NOT make up information or use knowledge outside the provided context.

CONTEXT:
{context}

QUESTION:
{question}

Provide a clear, concise answer (2-4 sentences). 
If relevant, mention which sources support your answer.
"""


def ask(question: str, n_results: int = 5, doc_type: str = None) -> dict:
    """
    Main entry point for the chat agent.

    Args:
        question: User's natural language question
        n_results: How many chunks to retrieve from vector store
        doc_type: Optional filter — "news", "research", or None for both

    Returns dict with:
        - answer: LLM generated response
        - sources: list of source documents used
        - chunks_found: number of relevant chunks retrieved
        - model: which LLM was used (for transparency)
    """
    if not question or not question.strip():
        return {
            "answer": "Please ask a question.",
            "sources": [],
            "chunks_found": 0,
            "model": CHAT_MODEL,
        }

    # Step 1: Retrieve relevant context from vector store
    retrieval = retrieve(question, n_results=n_results, doc_type=doc_type)

    # Step 2: If nothing relevant found, tell the user clearly
    if retrieval["chunks_found"] == 0:
        return {
            "answer": "I don't have enough information about that in my current knowledge base. "
            "Try asking about recent AI news or research papers after the daily digest runs.",
            "sources": [],
            "chunks_found": 0,
            "model": CHAT_MODEL,
        }

    # Step 3: Build the RAG prompt
    prompt = _build_prompt(question, retrieval["context"])

    # Step 4: Call Groq LLaMA
    try:
        response = _groq_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.3,  # WHY low temperature? We want factual answers,
            max_tokens=512,  # not creative ones. Lower = more focused.
        )

        answer = response.choices[0].message.content.strip()

        print(
            f"[chat_agent] Answered question using {retrieval['chunks_found']} chunks"
        )

        return {
            "answer": answer,
            "sources": retrieval["sources"],
            "chunks_found": retrieval["chunks_found"],
            "model": CHAT_MODEL,
        }

    except Exception as e:
        print(f"[chat_agent] Groq error: {e}")
        return {
            "answer": "Sorry, I encountered an error generating a response. Please try again.",
            "sources": [],
            "chunks_found": retrieval["chunks_found"],
            "model": CHAT_MODEL,
        }
