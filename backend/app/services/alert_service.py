"""Alert delivery: email (SMTP) or HTTP webhook."""
import json
import logging
import random
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _select_photos(all_frames: list[bytes], count: int) -> list[bytes]:
    """
    Select N frames.
    all_frames[0] = newest (LPUSH order), all_frames[-1] = entry frame.
    Returns frames in chronological order.
    """
    if not all_frames or count <= 0:
        return []
    if count >= len(all_frames):
        return list(reversed(all_frames))

    entry = all_frames[-1]
    last = all_frames[0]
    if count == 1:
        return [last]
    if count == 2:
        return [entry, last]

    middle_pool = all_frames[1:-1]
    n_middle = count - 2
    if len(middle_pool) <= n_middle:
        chosen = list(middle_pool)
    else:
        indices = sorted(random.sample(range(len(middle_pool)), n_middle))
        chosen = [middle_pool[i] for i in indices]
    return [entry] + list(reversed(chosen)) + [last]


async def send_alert(
    delivery_method: str,
    destination: str,
    subject: str,
    body_text: str,
    photos: list[bytes],
) -> None:
    if delivery_method == "email":
        await _send_email(destination, subject, body_text, photos)
    elif delivery_method == "webhook":
        await _send_webhook(destination, subject, body_text, photos)


async def _send_email(to: str, subject: str, body: str, photos: list[bytes]) -> None:
    if not settings.SMTP_HOST:
        logger.warning("SMTP_HOST not configured, skipping email")
        return

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to
    msg.attach(MIMEText(body, "plain", "utf-8"))
    for i, photo_bytes in enumerate(photos):
        img = MIMEImage(photo_bytes, name=f"photo_{i + 1}.jpg")
        msg.attach(img)

    last_err = None
    for attempt in range(3):
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                smtp.starttls()
                if settings.SMTP_USER:
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.sendmail(msg["From"], [to], msg.as_string())
            return
        except Exception as e:
            last_err = e
            logger.warning("Email attempt %d failed: %s", attempt + 1, e)
    raise RuntimeError(f"Email failed after 3 attempts: {last_err}")


async def _send_webhook(url: str, subject: str, body: str, photos: list[bytes]) -> None:
    last_err = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                if photos:
                    files = [("photos", (f"photo_{i+1}.jpg", p, "image/jpeg")) for i, p in enumerate(photos)]
                    data = {"subject": subject, "body": body}
                    await client.post(url, data=data, files=files)
                else:
                    await client.post(url, json={"subject": subject, "body": body})
            return
        except Exception as e:
            last_err = e
            logger.warning("Webhook attempt %d failed: %s", attempt + 1, e)
    raise RuntimeError(f"Webhook failed after 3 attempts: {last_err}")
