import africastalking
from django.conf import settings

africastalking.initialize(
    username=settings.AT_USERNAME,
    api_key=settings.AT_API_KEY,
)
sms = africastalking.SMS


REFERENCE_SMS_TEMPLATE = """BVSS Verification
{applicant_name} listed you as a business reference.

Reply with numbers only (e.g. 3 2 4):
1. How reliable is this person financially?
   1=Very unreliable  5=Very reliable
2. Do you know of any unpaid debts?
   1=Many debts  5=None I know of
3. How long have you known them?
   1=<6 months  5=5+ years

Reply: [Q1] [Q2] [Q3]
Token: {token}"""


STOKVEL_SMS_TEMPLATE = """BVSS Verification
Is {applicant_name} an active contributing member of your stokvel?

Reply YES or NO
Token: {token}"""


def send_reference_sms(reference, applicant_name: str) -> bool:
    """
    Send the three-question SMS to a reference.
    Returns True if AT API accepted the message.
    """
    message = REFERENCE_SMS_TEMPLATE.format(
        applicant_name=applicant_name,
        token=reference.verification_token,
    )
    try:
        response = sms.send(
            message=message,
            recipients=[reference.phone],
            sender_id=settings.AT_SENDER_ID,
        )
        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        return any(r.get("status") == "Success" for r in recipients)
    except Exception as exc:
        import logging
        logging.getLogger("bvss.verification").error(
            "SMS send failed for reference %s: %s", reference.id, exc
        )
        return False


def send_stokvel_sms(coordinator_phone: str, applicant_name: str, token: str) -> bool:
    message = STOKVEL_SMS_TEMPLATE.format(
        applicant_name=applicant_name,
        token=token,
    )
    try:
        response = sms.send(
            message=message,
            recipients=[coordinator_phone],
            sender_id=settings.AT_SENDER_ID,
        )
        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        return any(r.get("status") == "Success" for r in recipients)
    except Exception:
        return False


def parse_reference_reply(body: str) -> dict:
    """
    Parses a reference SMS reply body.
    Expected format: "3 4 5 TOKEN123" or "3 4 5"
    Returns {"q1": int, "q2": int, "q3": int} or {} on failure.
    """
    parts = body.strip().split()
    scores = []
    for part in parts:
        try:
            val = int(part)
            if 1 <= val <= 5:
                scores.append(val)
        except ValueError:
            pass

    if len(scores) >= 3:
        return {"q1": scores[0], "q2": scores[1], "q3": scores[2]}
    return {}


def score_from_reference_replies(q1: int, q2: int, q3: int) -> int:
    """
    Convert three 1–5 scores into a 0–100 trust composite.
    q1 = reliability, q2 = debt knowledge, q3 = relationship duration
    """
    raw = ((q1 + q2 + q3) / 15) * 100
    return round(raw)