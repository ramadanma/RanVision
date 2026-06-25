"""Alert delivery: email (SMTP) or HTTP webhook."""
import json
import random
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.config import settings


def _select_photos(all_frames: list[bytes], count: int) -> list[bytes]:
    """
    Select N frames from the accumulated list.
    all_frames[0] = newest (LPUSH order), all_frames[-1] = entry frame.
    Returns frames in chronological order.
    """
    if not all_frames or count <= 0:
        return []
    if count >= len(all_frames):
        return list(reversed(all_frames))  # chronological

    entry = all_frames[-1]
    last = all_frames[0]

    if count == 1:
        return [last]
    if count == 2:
        return [entry, last]

    middle_pool = all_frames[1:-1]
    n_middle = count - 2
    if len(middle_pool) <= n_middle:
        chosen_middle = list(middle_pool)
    else:
        # random sample, then sort by original index to maintain order
        indices = sorted(random.sample(range(len(middle_pool)), n_middle))
        chosen_middle = [middle_pool[i] for i in indices]

    return [entry] + list(reversed(chosen_middle)) + [last]


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
    smtp_host = getattr(settings, "SMTP_HOST", "localhost")
    smtp_port = int(getattr(settings, "SMTP_PORT", 587))
    smtp_user = getattr(settings, "SMTP_USER", "")
    smtp_pass = getattr(settings, "SMTP_PASSWORD", "")
    smtp_from = getattr(settings, "SMTP_FROM", smtp_user)

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to
    msg.attach(MIMEText(body, "plain"))

    for i, photo_bytes in enumerate(photos):
        img = MIMEImage(photo_bytes, name=f"photo_{i + 1}.jpg")
        msg.attach(img)

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        if smtp_user:
            smtp.login(smtp_user, smtp_pass)
        smtp.sendmail(smtp_from, [to], msg.as_string())


async def _send_webhook(url: str, subject: str, body: str, photos: list[bytes]) -> None:
    payload = {"subject": subject, "body": body, "photo_count": len(photos)}
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json=payload)
