import httpx

from ..core.config import settings


def send_telegram_message(message: str) -> bool:
    if not settings.TELEGRAM_ENABLED:
        return False

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }

    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
        return True
    except Exception as exc:
        print(f"[telegram] Failed to send message: {exc}")
        return False