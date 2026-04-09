import sys

sys.path.append("backend")

from app.services.fetcher import fetch_all_items
from app.services.summarizer import summarize_items
from app.services.email_sender import send_digest_to_subscriber

# Full pipeline test
print("Fetching...")
items = fetch_all_items()

print("Summarizing...")
summaries = summarize_items(items)

print("Sending email...")
# Replace with your own email to receive the test
send_digest_to_subscriber("vinitkhapekar09@gmail.com", summaries)
