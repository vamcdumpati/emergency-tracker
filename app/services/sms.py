import os, httpx, logging
logger = logging.getLogger(__name__)
FAST2SMS_URL = "https://www.fast2sms.com/dev/bulkV2"

async def send_tracking_sms(to_phone, sender_name, tracking_url, patient_name=None, hospital_name=None, message_type="emergency"):
    api_key = os.environ.get("FAST2SMS_API_KEY", "")
    if not api_key:
        logger.warning("FAST2SMS_API_KEY not set")
        return False
    if message_type == "emergency":
        message = f"EMERGENCY ALERT from {sender_name}!\nPatient: {patient_name or 'Unknown'}\nGoing to: {hospital_name or 'Hospital'}\nTrack live location:\n{tracking_url}"
    else:
        message = f"Hey Buddy Alert!\nPatient {patient_name or 'Unknown'} is being taken to {hospital_name or 'hospital'}.\nTrack live location:\n{tracking_url}"
    headers = {"authorization": api_key, "Content-Type": "application/json"}
    payload = {"route": "q", "message": message, "language": "english", "flash": 0, "numbers": to_phone}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(FAST2SMS_URL, json=payload, headers=headers)
            data = resp.json()
            return data.get("return", False)
    except Exception as exc:
        logger.exception("SMS send failed: %s", exc)
        return False
