import json
import socket
import time
from contextlib import contextmanager
from urllib.parse import urlparse

import mlflow
from google import genai
from ..core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

RETRY_ATTEMPTS = 3
RETRY_DELAY = 10  # seconds between retries


def _init_mlflow() -> bool:
    """Initialize MLflow once; disable tracking if the server is unavailable."""
    if not settings.MLFLOW_TRACKING_URL.strip():
        return False

    parsed = urlparse(settings.MLFLOW_TRACKING_URL)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    if host:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                pass
        except OSError:
            print(
                f"[summarizer] MLflow unreachable at {settings.MLFLOW_TRACKING_URL}; "
                "continuing without tracking"
            )
            return False

    try:
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URL)
        mlflow.set_experiment("daily-ai-digest")
        return True
    except Exception as e:
        print(f"[summarizer] MLflow unavailable; continuing without tracking: {e}")
        return False


@contextmanager
def _mlflow_run(enabled: bool):
    if not enabled:
        yield
        return

    try:
        with mlflow.start_run():
            yield
    except Exception as e:
        print(f"[summarizer] MLflow run failed; continuing without tracking: {e}")
        yield


def _mlflow_log(enabled: bool, log_fn, *args, **kwargs) -> None:
    if not enabled:
        return

    try:
        log_fn(*args, **kwargs)
    except Exception as e:
        print(f"[summarizer] MLflow log failed: {e}")


def build_prompt(items: list[dict]) -> str:
    items_text = ""
    for i, item in enumerate(items, 1):
        items_text += f"""
Item {i}:
Title: {item["title"]}
Summary: {item["summary"][:500]}
Source: {item["source"]}
Link: {item["link"]}
"""

    prompt = f"""
You are an AI newsletter writer. Your job is to explain recent AI/ML research and news in very simple language for a general audience.

Below are {len(items)} recent AI/ML items. For each one, return a JSON array where each object has exactly these fields:
- "headline": a short, engaging title (max 10 words)
- "simple_summary": explain it in 2-3 sentences as if talking to a curious 16-year-old. No jargon.
- "why_it_matters": 1-2 sentences on the real-world impact or why people should care
- "link": the original link

Return ONLY a valid JSON array. No markdown, no backticks, no explanation. Just the raw JSON array.

Items:
{items_text}
"""
    return prompt


def _call_gemini_with_retry(prompt: str) -> str | None:
    """
    Call Gemini with retry logic.
    Retries up to RETRY_ATTEMPTS times on 503/transient errors.
    Returns raw text on success, None if all attempts fail.
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            print(f"[summarizer] Gemini attempt {attempt}/{RETRY_ATTEMPTS}...")
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite", contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            is_transient = any(
                code in error_str for code in ["503", "429", "UNAVAILABLE", "quota"]
            )
            if is_transient and attempt < RETRY_ATTEMPTS:
                print(
                    f"[summarizer] Transient error on attempt {attempt}: {e}. "
                    f"Retrying in {RETRY_DELAY}s..."
                )
                time.sleep(RETRY_DELAY)
            else:
                print(f"[summarizer] Gemini error on attempt {attempt}: {e}")
                return None
    return None


def summarize_items(items: list[dict]) -> list[dict]:
    if not items:
        return []

    mlflow_enabled = _init_mlflow()
    items = items[:5]
    prompt = build_prompt(items)

    with _mlflow_run(mlflow_enabled):
        try:
            start_time = time.time()

            raw_text = _call_gemini_with_retry(prompt)
            if raw_text is None:
                print("[summarizer] All Gemini attempts failed.")
                return []

            latency = round(time.time() - start_time, 2)

            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]

            summaries = json.loads(raw_text)

            _mlflow_log(
                mlflow_enabled,
                mlflow.log_param,
                "model",
                "gemini-2.0-flash-lite",
            )
            _mlflow_log(mlflow_enabled, mlflow.log_param, "num_input_items", len(items))
            _mlflow_log(mlflow_enabled, mlflow.log_param, "prompt_length", len(prompt))
            _mlflow_log(mlflow_enabled, mlflow.log_metric, "latency_seconds", latency)
            _mlflow_log(
                mlflow_enabled,
                mlflow.log_metric,
                "num_summaries_returned",
                len(summaries),
            )
            _mlflow_log(mlflow_enabled, mlflow.log_text, prompt, "prompt.txt")
            _mlflow_log(mlflow_enabled, mlflow.log_text, raw_text, "response.txt")

            print(f"[summarizer] Got {len(summaries)} summaries in {latency}s")
            return summaries

        except json.JSONDecodeError as e:
            _mlflow_log(
                mlflow_enabled, mlflow.log_param, "error", f"JSON parse error: {e}"
            )
            print(f"[summarizer] JSON parse error: {e}")
            return []

        except Exception as e:
            _mlflow_log(mlflow_enabled, mlflow.log_param, "error", str(e))
            print(f"[summarizer] Unexpected error: {e}")
            return []
