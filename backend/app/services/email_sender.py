import resend
from ..core.config import settings

resend.api_key = settings.RESEND_API_KEY


def build_email_html(summaries: list[dict]) -> str:
    """Build a clean HTML email from the summaries."""

    items_html = ""
    for i, item in enumerate(summaries, 1):
        items_html += f"""
        <div style="margin-bottom: 32px; padding: 20px; background: #f9f9f9; border-left: 4px solid #4F46E5; border-radius: 4px;">
            <p style="font-size: 12px; color: #888; margin: 0 0 6px 0;">#{i}</p>
            <h2 style="font-size: 18px; color: #1a1a1a; margin: 0 0 10px 0;">{item.get("headline", "")}</h2>
            <p style="font-size: 15px; color: #333; line-height: 1.6; margin: 0 0 12px 0;">{item.get("simple_summary", "")}</p>
            <div style="background: #EEF2FF; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
                <strong style="color: #4F46E5;">Why it matters:</strong>
                <span style="color: #333;"> {item.get("why_it_matters", "")}</span>
            </div>
            <a href="{item.get("link", "#")}" style="color: #4F46E5; font-size: 14px;">Read more →</a>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1a1a1a;">

        <div style="text-align: center; margin-bottom: 32px;">
            <h1 style="font-size: 28px; color: #4F46E5; margin: 0;">🤖 Daily AI Digest</h1>
            <p style="color: #888; margin: 6px 0 0 0;">Your daily dose of AI/ML — explained simply</p>
        </div>

        {items_html}

        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center;">
            <p style="color: #aaa; font-size: 12px;">
                You're receiving this because you subscribed to Daily AI Digest.<br>
                <a href="https://your-domain.com/unsubscribe" style="color: #aaa;">Unsubscribe</a>
            </p>
        </div>

    </body>
    </html>
    """
    return html


def send_digest_to_subscriber(email: str, summaries: list[dict]) -> bool:
    """Send the digest email to a single subscriber."""
    try:
        html_content = build_email_html(summaries)

        resend.Emails.send(
            {
                "from": settings.FROM_EMAIL,
                "to": email,
                "subject": "🤖 Your Daily AI Digest is here!",
                "html": html_content,
            }
        )

        print(f"[email] Sent to {email}")
        return True

    except Exception as e:
        print(f"[email] Failed to send to {email}: {e}")
        return False


def send_digest_to_all(summaries: list[dict], subscribers: list[str]) -> dict:
    """Send digest to all active subscribers."""
    results = {"success": 0, "failed": 0}

    for email in subscribers:
        success = send_digest_to_subscriber(email, summaries)
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1

    print(f"[email] Done — {results['success']} sent, {results['failed']} failed")
    return results
