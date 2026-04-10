import json
import time
import mlflow
from google import genai
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URL)
mlflow.set_experiment("daily-ai-digest")


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


def summarize_items(items: list[dict]) -> list[dict]:
    if not items:
        return []

    items = items[:5]
    prompt = build_prompt(items)

    with mlflow.start_run():
        try:
            start_time = time.time()

            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview", contents=prompt
            )

            latency = round(time.time() - start_time, 2)
            raw_text = response.text.strip()

            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]

            summaries = json.loads(raw_text)

            # Log to MLflow
            mlflow.log_param("model", "gemini-3.1-flash-lite-preview")
            mlflow.log_param("num_input_items", len(items))
            mlflow.log_param("prompt_length", len(prompt))
            mlflow.log_metric("latency_seconds", latency)
            mlflow.log_metric("num_summaries_returned", len(summaries))
            mlflow.log_text(prompt, "prompt.txt")
            mlflow.log_text(raw_text, "response.txt")

            print(f"[summarizer] Got {len(summaries)} summaries in {latency}s")
            return summaries

        except json.JSONDecodeError as e:
            mlflow.log_param("error", f"JSON parse error: {e}")
            print(f"[summarizer] JSON parse error: {e}")
            return []

        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"[summarizer] Gemini error: {e}")
            return []
