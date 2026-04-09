import sys

sys.path.append("backend")

from backend.app.services.fetcher import fetch_all_items
from backend.app.services.summarizer import summarize_items

# Fetch raw items
print("Fetching items...")
items = fetch_all_items()

# Summarize with Gemini
print("Summarizing with Gemini...")
summaries = summarize_items(items)

# Print results
for i, s in enumerate(summaries, 1):
    print(f"\n{'=' * 60}")
    print(f"Item {i}: {s.get('headline')}")
    print(f"\nSummary: {s.get('simple_summary')}")
    print(f"\nWhy it matters: {s.get('why_it_matters')}")
    print(f"\nLink: {s.get('link')}")



