"""app/services/sms.py – Send SMS via Fast2SMS (free Indian SMS gateway)"""

import os
import httpx
import logging

logger = logging.getLogger(__name__)

FAST2SMS_URL = "https://www.fast2sms.com/dev/bulkV2"


async def send_tracking_sms(
    to_phone: str,
    sender_name: str,
    tracking_url: str,
) -> bool:
    """
    Send an emergency alert SMS with the live-tracking link.
    Returns True if sent successfully.

    Fast2SMS free account:
      • Sign up at https://fast2sms.com
      • Copy your API key from Dashboard → Dev API
      • Free credits are enough for testing; top-up is cheap (₹ 10 = ~130 SMS)
    """
    api_key = os.environ.get("FAST2SMS_API_KEY", "")
    if not api_key:
        logger.warning("FAST2SMS_API_KEY not set – SMS skipped")
        return False

    message = (
        f"🚨 EMERGENCY ALERT from {sender_name}!\n"
        f"They need help. Track their live location here:\n"
        f"{tracking_url}\n"
        f"(Link expires in 24 hours)"
    )

    headers = {"authorization": api_key, "Content-Type": "application/json"}
    payload = {
        "route": "q",           # quick / transactional route
        "message": message,
        "language": "english",
        "flash": 0,
        "numbers": to_phone,    # 10-digit number, no country code
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(FAST2SMS_URL, json=payload, headers=headers)
            data = resp.json()
            if data.get("return"):
                logger.info("SMS sent to %s", to_phone)
                return True
            else:
                logger.error("Fast2SMS error: %s", data)
                return False
    except Exception as exc:
        logger.exception("SMS send failed: %s", exc)
        return False
