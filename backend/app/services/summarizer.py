import json
import time
from google import genai
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_CANDIDATES = [
    "gemini-3.1-flash-lite-preview",
]


def build_prompt(items: list[dict]) -> str:
    """Build the prompt we send to Gemini for summarization."""

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


def summarize_items(items: list[dict]) -> list[dict]:
    """Sends the items to Gemini and gets back the summarized version."""

    if not items:
        return []

    items = items[:5]
    prompt = build_prompt(items)

    try:
        response = None
        latency = None
        last_error = None

        for model_name in MODEL_CANDIDATES:
            try:
                start_time = time.time()
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                latency = round(time.time() - start_time, 2)
                print(f"[summarizer] Using model: {model_name}")
                break
            except Exception as e:
                last_error = e

        if response is None:
            raise last_error or RuntimeError("No Gemini model could be used")

        raw_text = (response.text or "").strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        summaries = json.loads(raw_text)

        print(f"[summarizer] Got {len(summaries)} summaries in {latency}s")
        return summaries
    except json.JSONDecodeError as e:
        print(f"[summarizer] JSON decode error: {e}")
        print(f"Raw response was: {(response.text or '')[:300]}")
        return []
    except Exception as e:
        print(f"[summarizer] Error during summarization: {e}")
        return []
