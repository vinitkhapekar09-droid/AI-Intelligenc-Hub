# frontend/app.py
#
# WHY Streamlit?
# Streamlit lets us build a clean, interactive UI in pure Python.
# No HTML/CSS/JS needed. Perfect for ML/AI portfolio projects.

import streamlit as st
import requests
import os

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
# WHY? In Docker, API is at http://api:8000. Locally it's localhost:8000.
# Environment variable lets us switch without changing code.

st.set_page_config(
    page_title="AI Intelligence Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar Navigation ---
st.sidebar.title("🤖 AI Intelligence Hub")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["💬 Chat", "📰 Daily Digest", "📊 Status"],
)
st.sidebar.markdown("---")
st.sidebar.caption("Powered by Groq LLaMA + ChromaDB")


# ----------------------------------------------------------------
# PAGE 1: CHAT
# ----------------------------------------------------------------
if page == "💬 Chat":
    st.title("💬 Ask the AI Hub")
    st.markdown("Ask any question about recent AI news and research papers.")

    # Filter options
    col1, col2 = st.columns([3, 1])
    with col1:
        question = st.text_input(
            "Your question",
            placeholder="e.g. What is self-attention in transformers?",
        )
    with col2:
        doc_filter = st.selectbox(
            "Filter by",
            ["All", "Research", "News"],
        )

    if st.button("Ask", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Searching knowledge base..."):
                try:
                    doc_type = None
                    if doc_filter == "Research":
                        doc_type = "research"
                    elif doc_filter == "News":
                        doc_type = "news"

                    response = requests.post(
                        f"{API_BASE}/chat",
                        json={
                            "question": question,
                            "doc_type": doc_type,
                            "n_results": 5,
                        },
                        timeout=30,
                    )
                    try:
                        result = response.json()
                    except ValueError:
                        result = {}

                    if response.status_code != 200:
                        detail = result.get("detail") or response.text
                        st.error(f"Chat failed ({response.status_code}): {detail}")
                    elif "answer" not in result:
                        st.error("Chat response was missing the 'answer' field.")
                        st.write(result)
                    else:
                        # Display answer
                        st.markdown("### Answer")
                        st.success(result["answer"])

                        # Display sources
                        if result.get("sources"):
                            st.markdown("### Sources")
                            for source in result["sources"]:
                                st.markdown(
                                    f"- **{source['source']}** | "
                                    f"[{source['title']}]({source['url']}) "
                                    f"`{source['doc_type']}`"
                                )

                        # Metadata
                        st.caption(
                            f"Retrieved {result.get('chunks_found', 0)} relevant chunks · "
                            f"Model: {result.get('model', 'unknown')}"
                        )

                except requests.exceptions.ConnectionError:
                    st.error(
                        "Cannot connect to backend. Make sure FastAPI is running on port 8000."
                    )
                except Exception as e:
                    st.error(f"Error: {e}")


# ----------------------------------------------------------------
# PAGE 2: DAILY DIGEST
# ----------------------------------------------------------------
elif page == "📰 Daily Digest":
    st.title("📰 Daily AI Digest")
    st.markdown("Trigger the pipeline or check the latest digest status.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Trigger Pipeline")
        st.markdown("Runs the full pipeline: fetch → summarize → email → RAG ingest.")
        if st.button("🚀 Run Daily Digest", type="primary"):
            with st.spinner("Triggering pipeline..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/trigger-digest",
                        timeout=10,
                    )
                    try:
                        result = response.json()
                    except ValueError:
                        result = {}

                    if response.status_code == 200:
                        st.success(
                            f"Pipeline triggered! Task ID: `{result.get('task_id', 'N/A')}`"
                        )
                        st.caption(
                            "Pipeline runs asynchronously via Celery. Check Status page for results."
                        )
                    else:
                        detail = result.get("detail") or response.text
                        st.error(f"Trigger failed ({response.status_code}): {detail}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        st.markdown("### Digest Status")
        if st.button("🔄 Refresh Status"):
            with st.spinner("Fetching status..."):
                try:
                    response = requests.get(
                        f"{API_BASE}/daily-digest",
                        timeout=10,
                    )
                    result = response.json()
                    vs = result.get("vector_store", {})

                    st.metric("Total Chunks in KB", vs.get("total_chunks", 0))
                    st.metric("Collection", vs.get("collection_name", "N/A"))
                    st.caption(f"Storage: {vs.get('storage_path', 'N/A')}")

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend.")
                except Exception as e:
                    st.error(f"Error: {e}")


# ----------------------------------------------------------------
# PAGE 3: STATUS
# ----------------------------------------------------------------
elif page == "📊 Status":
    st.title("📊 System Status")

    if st.button("🔄 Check Health"):
        with st.spinner("Checking..."):
            # Check API health
            try:
                response = requests.get(f"{API_BASE}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ FastAPI backend is healthy")
                else:
                    st.error("❌ FastAPI backend returned an error")
            except requests.exceptions.ConnectionError:
                st.error("❌ FastAPI backend is unreachable")

            # Check vector store
            try:
                response = requests.get(f"{API_BASE}/daily-digest", timeout=5)
                result = response.json()
                vs = result.get("vector_store", {})
                st.info(f"📦 Vector store: {vs.get('total_chunks', 0)} chunks stored")
            except Exception:
                st.warning("⚠️ Could not fetch vector store stats")

    st.markdown("---")
    st.markdown("### Architecture")
    st.code("""
    Celery Beat (7AM IST)
          ↓
    fetch → normalize → summarize → email → chunk → embed → Chroma
                                                              ↓
    User → Streamlit UI → POST /chat → retrieve → Groq LLaMA → answer
    """)
