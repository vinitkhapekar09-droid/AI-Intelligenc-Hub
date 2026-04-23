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
    - More conversational tone makes it feel human-like
    """
    history_text = ""
    if history:
        # Limit history to prevent token overflow and maintain focus
        history_items = history[-MAX_HISTORY_TURNS:]
        history_text = "\n".join(
            f"{item['role'].capitalize()}: {item['text']}" for item in history_items
        )
        history_text = f"📚 CONVERSATION HISTORY:\n{history_text}\n\n"

    return f"""You are a friendly and knowledgeable AI research assistant specializing in AI and ML news and research. 
Your personality: helpful, conversational, and honest about your limitations.
You speak naturally like a human, not like a robot.

IMPORTANT GUIDELINES:
✓ Use the context below to answer questions - it's your knowledge base
✓ If the context doesn't have the info, just say you don't have it - don't make things up
✓ Keep answers conversational and human-like (2-4 sentences usually)
✓ When mentioning sources, weave them naturally into your response
✓ Use "I" sometimes (e.g., "I found that...", "I don't have data on...")
✓ Show personality - ask follow-ups if the question seems incomplete

{history_text}📖 CONTEXT TO USE:
{context}

🤔 THE QUESTION:
{question}

Remember: Be helpful, be honest, be conversational. If you're not sure about something, say so!
"""


def _is_greeting(question: str) -> bool:
    """Check if the question is a greeting or off-topic."""
    greetings = ["hello", "hi", "hey", "hii", "hiii", "greetings", "howdy", "what's up", "yo", "sup", "hey there", "good morning", "good afternoon", "good evening"]
    normalized = question.lower().strip()
    return any(greeting in normalized for greeting in greetings)


def _handle_greeting(question: str) -> dict:
    """Handle greetings with a friendly, conversational response."""
    responses = [
        "Hey! 👋 I'm here to help you explore the latest in AI and machine learning research. What's on your mind?",
        "Hi there! 👋 Got any questions about AI news or research papers? I'm all ears!",
        "Hey! Welcome to the AI hub. What would you like to know about AI/ML today?",
        "Good to see you! Ready to dive into some AI research or news? Just ask away!",
        "Hey! 👋 I'm your AI research assistant. What can I help you discover today?",
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


def _validate_response(answer: str) -> bool:
    """Validate that the response meets quality standards."""
    if not answer or len(answer) < 10:
        return False
    if len(answer) > 2000:
        return False
    return True


def ask(question: str, n_results: int = 5, doc_type: str = None, history: list | None = None) -> dict:
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
    
    # Handle greetings and off-topic messages
    if _is_greeting(question):
        return _handle_greeting(question)

    # Step 2: Try to improve the query if it looks like a follow-up
    enhanced_question = question
    is_followup = _is_follow_up(question)
    
    if is_followup and history:
        print(f"[chat_agent] Follow-up detected, using history ({len(history)} messages)")
        enhanced_question = _improve_query_with_history(question, history)
        print(f"[chat_agent] Enhanced question: '{question}' → '{enhanced_question}'")

    # Step 3: Retrieve relevant context from vector store
    retrieval = retrieve(enhanced_question, n_results=n_results, doc_type=doc_type)

    # Step 4: If nothing found with enhanced question, try with original
    if retrieval["chunks_found"] == 0 and enhanced_question != question:
        retrieval = retrieve(question, n_results=n_results, doc_type=doc_type)
    
    # Step 5: If STILL nothing, try to find ANY related content from history
    if retrieval["chunks_found"] == 0 and history and is_followup:
        # Try searching with previous questions for context
        for i in range(len(history) - 1, max(len(history) - 5, -1), -1):
            if history[i].get("role") == "user":
                prev_q = history[i].get("text", "").strip()
                if prev_q and prev_q != question:
                    retrieval = retrieve(prev_q, n_results=n_results, doc_type=doc_type)
                    if retrieval["chunks_found"] > 0:
                        break

    # Step 6: If still nothing found, provide a helpful response
    if retrieval["chunks_found"] == 0:
        # If this is a follow-up and we have history, acknowledge what we discussed
        if is_followup and history:
            # Find what we were discussing
            last_user_q = None
            for i in range(len(history) - 1, -1, -1):
                if history[i].get("role") == "user":
                    last_user_q = history[i].get("text", "").strip()
                    break
            
            if last_user_q and last_user_q != question:
                return {
                    "answer": f"I've shared what I know about '{last_user_q}' from the knowledge base. Unfortunately, I don't have more information on that specific topic. Would you like to ask about something else in AI/ML?",
                    "sources": [],
                    "chunks_found": 0,
                    "model": CHAT_MODEL,
                }
        
        # Default response for when we have no information
        suggestions = [
            "I don't have data on that just yet. The knowledge base mostly has content from recent digests. Try asking about recent AI news or research papers?",
            "Hmm, I couldn't find anything about that in my current knowledge. Have you tried asking about a specific AI research topic or recent news?",
            "That's an interesting question, but I don't have information about it in the knowledge base. What about asking me something related to AI/ML research?",
        ]
        import random
        return {
            "answer": random.choice(suggestions),
            "sources": [],
            "chunks_found": 0,
            "model": CHAT_MODEL,
        }

    # Step 7: Build the RAG prompt with conversation history
    prompt = _build_prompt(question, retrieval["context"], history=history)

    # Step 8: Call Groq LLaMA with retry logic and better error handling
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
                temperature=0.5,  # Slightly higher for more conversational tone
                max_tokens=512,
            )

            answer = response.choices[0].message.content.strip()
            
            # Validate response quality
            if not _validate_response(answer):
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    answer = "I had trouble generating a clear response. Could you try rewording your question?"
            
            print(f"[chat_agent] Answered using {retrieval['chunks_found']} chunks (attempt {attempt + 1})")
            break
            
        except Exception as e:
            last_error = e
            print(f"[chat_agent] Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
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
