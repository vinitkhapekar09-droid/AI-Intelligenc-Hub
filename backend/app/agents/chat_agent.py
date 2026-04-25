# agents/chat_agent.py
#
# WHY THIS FILE EXISTS:
# This is the RAG-based chat agent — the core intelligence of the system.
# It combines retrieved context from our vector store with Groq LLaMA
# to answer user questions grounded in real, ingested AI/ML content.
#
# FLOW: question → retrieve context → build prompt → LLM → answer + sources

import re
import asyncio
from groq import AsyncGroq
from ..core.config import settings
from ..rag.retriever import retrieve

# WHY module level?
# Groq client is stateless and thread-safe — safe to initialize once.
# Unlike MLflow, it doesn't make network calls at initialization.
_groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

# The model we use for chat responses.
# llama-3.1-8b-instant is fast and free on Groq.
# WHY not 70b? 8b is sufficient for RAG — the context does the heavy lifting.
CHAT_MODEL = "llama-3.1-8b-instant"

# Safety limits
MAX_QUESTION_LENGTH = 1000
MAX_HISTORY_TURNS = 40
MAX_RECENT_HISTORY_TURNS = 16
MAX_RETRIES = 2
RETRY_DELAY = 1.0
DEFAULT_SUMMARY_QUERY = "Summarize the most important AI news and research updates in the selected knowledge base."
GENERIC_SUMMARY_TERMS = {
    "news",
    "papers",
    "research",
    "updates",
    "today",
    "latest",
    "digest",
    "summary",
}


def _sanitize_input(text: str) -> str:
    """Sanitize user input to prevent abuse."""
    if not text:
        return ""

    # Remove excessive whitespace
    text = " ".join(text.split())

    # Truncate if too long
    if len(text) > MAX_QUESTION_LENGTH:
        text = text[:MAX_QUESTION_LENGTH]

    return text.strip()


def _is_spam_or_abuse(question: str) -> bool:
    """Detect potential spam or abuse patterns."""
    # Check for repetitive characters (e.g., "aaaaaaa")
    if re.search(r"(.)\1{10,}", question):
        return True

    # Check for excessive punctuation
    if len(re.sub(r"[^!?.]", "", question)) > len(question) * 0.5:
        return True

    # Check for URL spam
    if re.search(r"https?://|www\.", question):
        return True

    return False


def _format_history(history: list | None) -> str:
    if not history:
        return ""

    history_items = history[-MAX_HISTORY_TURNS:]
    recent_items = history_items[-MAX_RECENT_HISTORY_TURNS:]
    earlier_items = history_items[:-MAX_RECENT_HISTORY_TURNS]
    formatted_items = []
    for item in recent_items:
        role = item.get("role", "user").capitalize()
        text = item.get("text", "").strip()
        if not text:
            continue
        formatted_items.append(f"{role}: {text}")

    if not formatted_items and not earlier_items:
        return ""

    summary_lines = []
    if earlier_items:
        earlier_user_topics = []
        for item in earlier_items:
            if item.get("role") == "user":
                text = item.get("text", "").strip()
                if text:
                    earlier_user_topics.append(text[:120])

        if earlier_user_topics:
            unique_topics = []
            seen = set()
            for topic in reversed(earlier_user_topics):
                if topic not in seen:
                    unique_topics.append(topic)
                    seen.add(topic)
                if len(unique_topics) >= 6:
                    break
            unique_topics.reverse()
            summary_lines.append("EARLIER THREAD TOPICS: " + " | ".join(unique_topics))

    history_sections = []
    if summary_lines:
        history_sections.append("\n".join(summary_lines))
    if formatted_items:
        history_sections.append("RECENT EXCHANGE:\n" + "\n".join(formatted_items))

    return "CONVERSATION HISTORY:\n" + "\n\n".join(history_sections) + "\n\n"


def _build_prompt(
    question: str,
    context: str,
    history: list | None = None,
    issue_date: str | None = None,
) -> str:
    """
    Builds the RAG prompt with optional conversation history.

    WHY this structure?
    - Conversation history gives the model context for follow-up questions
    - Explicit context section prevents hallucination
    - "If the context doesn't contain..." prevents confident wrong answers
    - More conversational tone makes it feel human-like
    """
    history_text = _format_history(history)

    scope_text = (
        f"The user asked you to focus on the issue dated {issue_date}.\n\n"
        if issue_date
        else ""
    )

    return f"""You are a professional AI research assistant.
Your job is to help the user analyze AI news and research papers with accuracy, clarity, and good judgment.

RULES:
- Base your answer on the supplied context and the conversation history.
- Treat the conversation history as working memory for follow-up questions and references like "that", "this", "the paper", or "what else".
- If the context is insufficient, say so directly and propose a better next question.
- Do not invent facts, citations, experiments, or conclusions.
- Prefer precise, well-structured answers over casual chatter.
- For broad questions, synthesize the main themes rather than listing random details.
- When useful, distinguish between news coverage, paper claims, and your own inference.
- If the user's request is ambiguous, answer with the best grounded interpretation and keep it useful.

STYLE:
- Professional, concise, and analytical.
- Usually 1 short paragraph plus 2-5 crisp bullets when summarizing.
- Reference sources naturally and only when they materially support the answer.

{scope_text}{history_text}CONTEXT TO USE:
{context}

USER QUESTION:
{question}
"""


def _is_greeting(question: str) -> bool:
    """Check if the question is a greeting without false substring matches."""
    normalized = question.lower().strip()
    simple_greetings = {
        "hello",
        "hi",
        "hey",
        "hii",
        "hiii",
        "greetings",
        "howdy",
        "yo",
        "sup",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "what's up",
    }
    return normalized in simple_greetings


def _is_identity_question(question: str) -> bool:
    normalized = question.lower().strip()
    identity_patterns = [
        "what is your name",
        "what's your name",
        "who are you",
        "tell me your name",
        "your name",
        "what should i call you",
    ]
    return any(pattern in normalized for pattern in identity_patterns)


def _handle_identity_question() -> dict:
    return {
        "answer": (
            "I'm AI Intelligence Hub's research assistant. I help analyze the daily AI issue, "
            "summarize news and papers, compare developments, and answer follow-up questions using the saved thread context."
        ),
        "sources": [],
        "chunks_found": 0,
        "model": CHAT_MODEL,
    }


def _handle_greeting(question: str) -> dict:
    """Handle greetings with a more professional opening."""
    responses = [
        "Hello. I can help you analyze today's AI news, compare research papers, or summarize the selected issue.",
        "Hello. Ask me to summarize the issue, explain a paper, compare developments, or pull out the most important news.",
        "Hi. I can help with AI news analysis, paper summaries, follow-up questions, or broader research across the archive.",
    ]

    import random

    return {
        "answer": random.choice(responses),
        "sources": [],
        "chunks_found": 0,
        "model": CHAT_MODEL,
    }


def _is_follow_up(question: str) -> bool:
    """Check if this looks like a follow-up question."""
    follow_up_patterns = [
        "tell me more",
        "what about",
        "explain that",
        "how so",
        "why",
        "can you",
        "could you",
        "what do you think",
        "elaborate",
        "details",
        "example",
        "specifically",
        "basically",
        "so like",
        "what else",  # IMPORTANT: Must detect this!
        "continue",
        "go on",
        "more",
        "further",
        "and",
        "what's",
        "how about",
        "expand",
    ]
    normalized = question.lower()
    return any(pattern in normalized for pattern in follow_up_patterns)


def _improve_query_with_history(question: str, history: list) -> str:
    """Enhance a vague question using conversation history."""
    if not history or len(history) == 0:
        return question

    # For very short follow-ups, find what we were talking about
    if len(question) < 30:
        # Look for the last non-greeting assistant response
        for i in range(len(history) - 1, -1, -1):
            if history[i].get("role") == "assistant":
                last_response = history[i].get("text", "")
                # Extract first sentence for context
                first_sentence = last_response.split(".")[0]
                if first_sentence and len(first_sentence) > 10:
                    return f"{question} about {first_sentence[:60]}"

        # If just saying "what else", look for the previous user question
        if question.lower() in ["what else", "tell me more", "go on", "continue"]:
            for i in range(len(history) - 1, -1, -1):
                if history[i].get("role") == "user":
                    last_question = history[i].get("text", "")
                    return f"{question} about {last_question[:60]}"

    return question


def _extract_last_user_topic(history: list | None) -> str | None:
    if not history:
        return None

    for item in reversed(history):
        if item.get("role") == "user":
            text = item.get("text", "").strip()
            if text:
                return text

    return None


def _is_generic_summary_request(question: str) -> bool:
    normalized = re.sub(r"[^a-z0-9\s]", " ", question.lower()).strip()
    if not normalized:
        return False

    if normalized in GENERIC_SUMMARY_TERMS:
        return True

    generic_patterns = [
        "what's new",
        "what is new",
        "what happened",
        "summarize today's",
        "summarize today",
        "top news",
        "latest news",
        "latest papers",
        "key updates",
    ]
    return any(pattern in normalized for pattern in generic_patterns)


def _rewrite_query(
    question: str, history: list | None = None, issue_date: str | None = None
) -> str:
    normalized = question.strip()

    if _is_generic_summary_request(normalized):
        if issue_date:
            return f"Summarize the most important AI news and research updates from the issue dated {issue_date}."
        return DEFAULT_SUMMARY_QUERY

    if history and len(normalized.split()) <= 6:
        last_user_topic = _extract_last_user_topic(history)
        if last_user_topic and last_user_topic.lower() != normalized.lower():
            if normalized.lower() in {
                "why",
                "how",
                "more",
                "details",
                "expand",
                "what else",
            }:
                return f"{normalized} about {last_user_topic}"

    return normalized


def _fallback_no_context_answer(
    question: str, history: list | None = None, issue_date: str | None = None
) -> str:
    last_topic = _extract_last_user_topic(history)
    scope_text = f" for the issue dated {issue_date}" if issue_date else ""

    if last_topic and last_topic.lower() != question.lower():
        return (
            f"I do not have enough grounded context{scope_text} to answer that follow-up confidently. "
            f"If you want, ask me to summarize or analyze '{last_topic}' more specifically."
        )

    return (
        f"I could not find enough relevant context{scope_text} to answer that well. "
        "Try asking for a summary of the issue, the top news, the main papers, or a specific topic or company."
    )


def _validate_response(answer: str) -> bool:
    """Validate that the response meets quality standards."""
    if not answer or len(answer) < 10:
        return False
    if len(answer) > 2000:
        return False
    return True


async def ask(
    question: str,
    n_results: int = 5,
    doc_type: str = None,
    history: list | None = None,
    issue_date: str | None = None,
) -> dict:
    """
    Main entry point for the chat agent with memory support.

    Args:
        question: User's natural language question
        n_results: How many chunks to retrieve from vector store
        doc_type: Optional filter — "news", "research", or None for both
        history: Optional list of previous chat messages for persistent memory

    Returns dict with:
        - answer: LLM generated response (conversational and human-like)
        - sources: list of source documents used
        - chunks_found: number of relevant chunks retrieved
        - model: which LLM was used (for transparency)
    """
    # Sanitize input
    question = _sanitize_input(question)

    if not question or not question.strip():
        return {
            "answer": "Hmm, looks like that was empty. Go ahead and ask me anything about AI news or research!",
            "sources": [],
            "chunks_found": 0,
            "model": CHAT_MODEL,
        }

    # Detect spam or abuse
    if _is_spam_or_abuse(question):
        return {
            "answer": "I couldn't understand that input. Could you rephrase your question about AI/ML research or news?",
            "sources": [],
            "chunks_found": 0,
            "model": CHAT_MODEL,
        }

    # Handle greetings and identity/meta messages before retrieval
    if _is_greeting(question):
        return _handle_greeting(question)
    if _is_identity_question(question):
        return _handle_identity_question()

    # Step 2: Rewrite vague or generic queries into better retrieval prompts
    enhanced_question = _rewrite_query(question, history=history, issue_date=issue_date)
    is_followup = _is_follow_up(question)

    if is_followup and history:
        print(
            f"[chat_agent] Follow-up detected, using history ({len(history)} messages)"
        )
        enhanced_question = _improve_query_with_history(question, history)
        print(f"[chat_agent] Enhanced question: '{question}' → '{enhanced_question}'")

    # Step 3: Retrieve relevant context from vector store
    retrieval = retrieve(
        enhanced_question,
        n_results=n_results,
        doc_type=doc_type,
        issue_date=issue_date,
    )

    # Step 4: If nothing found with enhanced question, try with original
    if retrieval["chunks_found"] == 0 and enhanced_question != question:
        retrieval = retrieve(
            question,
            n_results=n_results,
            doc_type=doc_type,
            issue_date=issue_date,
        )

    # Step 4b: Generic summary fallback for short intents like "news" or "papers"
    if retrieval["chunks_found"] == 0 and _is_generic_summary_request(question):
        retrieval = retrieve(
            DEFAULT_SUMMARY_QUERY
            if not issue_date
            else f"{DEFAULT_SUMMARY_QUERY} Focus on {issue_date}.",
            n_results=max(n_results, 8),
            doc_type=doc_type,
            issue_date=issue_date,
        )

    # Step 5: If STILL nothing, try to find ANY related content from history
    if retrieval["chunks_found"] == 0 and history and is_followup:
        # Try searching with previous questions for context
        for i in range(len(history) - 1, max(len(history) - 5, -1), -1):
            if history[i].get("role") == "user":
                prev_q = history[i].get("text", "").strip()
                if prev_q and prev_q != question:
                    retrieval = retrieve(
                        prev_q,
                        n_results=n_results,
                        doc_type=doc_type,
                        issue_date=issue_date,
                    )
                    if retrieval["chunks_found"] > 0:
                        break

    # Step 6: If still nothing found, provide a grounded fallback
    if retrieval["chunks_found"] == 0:
        return {
            "answer": _fallback_no_context_answer(
                question,
                history=history,
                issue_date=issue_date,
            ),
            "sources": [],
            "chunks_found": 0,
            "model": CHAT_MODEL,
        }

    # Step 7: Build the RAG prompt with conversation history
    prompt = _build_prompt(
        question,
        retrieval["context"],
        history=history,
        issue_date=issue_date,
    )

    # Step 8: Call Groq LLaMA with retry logic and better error handling
    answer = None

    for attempt in range(MAX_RETRIES):
        try:
            response = await _groq_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a rigorous research assistant. Answer only from the provided context and conversation memory.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.2,
                max_tokens=700,
            )

            answer = response.choices[0].message.content.strip()

            # Validate response quality
            if not _validate_response(answer):
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                else:
                    answer = "I had trouble generating a clear response. Could you try rewording your question?"

            print(
                f"[chat_agent] Answered using {retrieval['chunks_found']} chunks (attempt {attempt + 1})"
            )
            break

        except Exception as e:
            print(f"[chat_agent] Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
                continue

    if answer is None:
        return {
            "answer": "Oops, I'm having trouble connecting right now. Give me a second and try again!",
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
