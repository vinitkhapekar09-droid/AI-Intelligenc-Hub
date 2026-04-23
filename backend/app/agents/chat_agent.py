# agents/chat_agent.py
#
# WHY THIS FILE EXISTS:
# This is the RAG-based chat agent — the core intelligence of the system.
# It combines retrieved context from our vector store with Groq LLaMA
# to answer user questions grounded in real, ingested AI/ML content.
#
# FLOW: question → retrieve context → build prompt → LLM → answer + sources

import re
import time
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

# Safety limits
MAX_QUESTION_LENGTH = 1000
MAX_HISTORY_TURNS = 10
MAX_RETRIES = 2
RETRY_DELAY = 1.0


def _sanitize_input(text: str) -> str:
    """Sanitize user input to prevent abuse."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = " ".join(text.split())
    
    # Truncate if too long
    if len(text) > MAX_QUESTION_LENGTH:
        text = text[:MAX_QUESTION_LENGTH]
    
    # Remove potentially harmful patterns
    text = re.sub(r'(<script|javascript:|onerror=)', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def _is_spam_or_abuse(question: str) -> bool:
    """Detect potential spam or abuse patterns."""
    # Check for repetitive characters (e.g., "aaaaaaa")
    if re.search(r'(.)\1{10,}', question):
        return True
    
    # Check for excessive punctuation
    if len(re.sub(r'[^!?.]', '', question)) > len(question) * 0.5:
        return True
    
    # Check for URL spam
    if re.search(r'https?://|www\.', question):
        return True
    
    return False


def _build_prompt(question: str, context: str, history: list | None = None) -> str:
    """
    Builds the RAG prompt with optional conversation history.

    WHY this structure?
    - Conversation history gives the model context for follow-up questions
    - Explicit context section prevents hallucination
    - "If the context doesn't contain..." prevents confident wrong answers
    - Asking for concise answers keeps responses readable
    """
    history_text = ""
    if history:
        # Limit history to prevent token overflow and maintain focus
        history_items = history[-MAX_HISTORY_TURNS:]
        history_text = "\n".join(
            f"{item['role'].capitalize()}: {item['text']}" for item in history_items
        )
        history_text = f"CONVERSATION HISTORY:\n{history_text}\n\n"

    return f"""You are an AI research assistant for an AI/ML intelligence hub.
You help users understand the latest AI news and research papers.
Be concise, accurate, and honest about the limits of your knowledge.

Use ONLY the context below to answer the question.
If the context doesn't contain enough information to answer,
say "I don't have enough information about that in my current knowledge base."
Do NOT make up information or use knowledge outside the provided context.
Do NOT speculate about sources not mentioned in the context.

{history_text}CONTEXT:
{context}

QUESTION:
{question}

Provide a clear, concise answer (2-4 sentences).
If relevant, mention which sources support your answer.
Format your response in plain text without markdown.
"""


def _is_greeting(question: str) -> bool:
    """Check if the question is a greeting or off-topic."""
    greetings = ["hello", "hi", "hey", "hii", "hiii", "greetings", "howdy", "what's up", "yo", "sup"]
    normalized = question.lower().strip()
    return any(greeting in normalized for greeting in greetings)


def _handle_greeting(question: str) -> dict:
    """Handle greetings with a friendly response."""
    responses = {
        "hi": "Hey there! 👋 I'm here to help you learn about the latest AI news and research. What would you like to know?",
        "hello": "Hello! Welcome to the AI Intelligence Hub. Ask me anything about AI/ML research and news.",
        "hey": "Hey! Ready to explore some AI insights? What interests you?",
        "what's up": "Not much, just here to help! What AI topics are you curious about?",
    }
    
    normalized = question.lower().strip()
    for greeting, response in responses.items():
        if greeting in normalized:
            return {
                "answer": response,
                "sources": [],
                "chunks_found": 0,
                "model": CHAT_MODEL,
            }
    
    # Default friendly response
    return {
        "answer": "Hey! I'm an AI assistant specialized in AI news and research. Feel free to ask me about the latest developments in machine learning, AI research papers, or industry news!",
        "sources": [],
        "chunks_found": 0,
        "model": CHAT_MODEL,
    }


def _validate_response(answer: str) -> bool:
    """Validate that the response meets quality standards."""
    if not answer or len(answer) < 10:
        return False
    if len(answer) > 2000:
        return False
    return True


def ask(question: str, n_results: int = 5, doc_type: str = None, history: list | None = None) -> dict:
    """
    Main entry point for the chat agent.

    Args:
        question: User's natural language question
        n_results: How many chunks to retrieve from vector store
        doc_type: Optional filter — "news", "research", or None for both
        history: Optional list of previous chat messages for short-term context

    Returns dict with:
        - answer: LLM generated response
        - sources: list of source documents used
        - chunks_found: number of relevant chunks retrieved
        - model: which LLM was used (for transparency)
    """
    # Sanitize input
    question = _sanitize_input(question)
    
    if not question or not question.strip():
        return {
            "answer": "Please ask a question.",
            "sources": [],
            "chunks_found": 0,
            "model": CHAT_MODEL,
        }
    
    # Detect spam or abuse
    if _is_spam_or_abuse(question):
        return {
            "answer": "I couldn't process that input. Please ask a clear question about AI news or research.",
            "sources": [],
            "chunks_found": 0,
            "model": CHAT_MODEL,
        }
    
    # Handle greetings and off-topic messages
    if _is_greeting(question):
        return _handle_greeting(question)

    # Step 1: Retrieve relevant context from vector store
    retrieval = retrieve(question, n_results=n_results, doc_type=doc_type)

    # Step 2: If vague query returns nothing, improve it using conversation history
    if retrieval["chunks_found"] == 0 and history and len(history) > 0:
        # Try to improve the query by extracting context from previous turns
        # Look at the last assistant response for keywords to add context
        last_assistant = None
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                last_assistant = msg.get("text", "")
                break
        
        # If we found previous context, try a richer query combining them
        if last_assistant:
            enriched_question = f"{question} about {last_assistant[:100]}"
            retrieval = retrieve(enriched_question, n_results=n_results, doc_type=doc_type)

    # Step 3: If still nothing found, return helpful message
    if retrieval["chunks_found"] == 0:
        return {
            "answer": "I don't have enough information about that in my current knowledge base. "
            "Try asking about recent AI news or research papers after the daily digest runs.",
            "sources": [],
            "chunks_found": 0,
            "model": CHAT_MODEL,
        }

    # Step 4: Build the RAG prompt
    prompt = _build_prompt(question, retrieval["context"], history=history)

    # Step 5: Call Groq LLaMA with retry logic
    answer = None
    last_error = None
    
    for attempt in range(MAX_RETRIES):
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
            
            # Validate response quality
            if not _validate_response(answer):
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    answer = "I generated a response but it didn't meet quality standards. Please try rephrasing your question."
            
            print(f"[chat_agent] Answered question using {retrieval['chunks_found']} chunks (attempt {attempt + 1})")
            break
            
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            else:
                print(f"[chat_agent] Failed after {MAX_RETRIES} attempts: {e}")

    if answer is None:
        return {
            "answer": "Sorry, I encountered an error generating a response. Please try again in a moment.",
            "sources": [],
            "chunks_found": retrieval["chunks_found"],
            "model": CHAT_MODEL,
        }

    return {
        "answer": answer,
        "sources": retrieval["sources"],
        "chunks_found": retrieval["chunks_found"],
        "model": CHAT_MODEL,
    }
