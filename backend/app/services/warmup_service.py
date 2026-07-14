"""Email warm-up service — gradually builds sender reputation."""

import random
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.campaign import SMTPConfig, EmailEvent, Campaign
from app.models.user import User

logger = logging.getLogger(__name__)

# Warm-up email templates — friendly, non-salesy emails
WARMUP_SUBJECTS = [
    "Quick hello",
    "Checking in",
    "Thought you'd find this interesting",
    "Following up",
    "Just wanted to share this",
    "Hope you're doing well",
    "Quick question",
    "Came across something useful",
]

WARMUP_BODIES = [
    "<p>Hi {name},</p><p>Just wanted to check in and see how things are going. Hope all is well!</p><p>Best</p>",
    "<p>Hey {name},</p><p>I came across this article and thought of you. Hope your week is going great!</p><p>Cheers</p>",
    "<p>Hi {name},</p><p>Quick question — have you tried the new coffee shop on Main Street? Heard great things.</p><p>Best</p>",
    "<p>Hey {name},</p><p>Just wanted to say thanks for connecting last week. Really appreciated the chat!</p><p>Best regards</p>",
    "<p>Hi {name},</p><p>Hope you're having a productive week. Let me know if you need anything!</p><p>Best</p>",
]

# Pool of warm-up receiving addresses (in production, use a real pool)
WARMUP_RECEIVERS = [
    "warmup1@mailwarm.co",
    "warmup2@mailwarm.co",
    "warmup3@mailwarm.co",
    "warmup4@mailwarm.co",
    "warmup5@mailwarm.co",
]


class WarmupSchedule:
    """Defines warm-up sending schedule per day."""

    SCHEDULE = {
        1: 5,    # Day 1: 5 emails
        2: 8,    # Day 2: 8 emails
        3: 12,   # Day 3: 12 emails
        4: 18,   # Day 4: 18 emails
        5: 25,   # Day 5: 25 emails
        6: 35,   # Day 6: 35 emails
        7: 50,   # Day 7: 50 emails
        8: 70,   # Day 8: 70 emails
        9: 100,  # Day 9: 100 emails
        10: 150, # Day 10: 150 emails
        11: 200, # Day 11: 200 emails
        12: 250, # Day 12: 250 emails
        13: 300, # Day 13: 300 emails
        14: 400, # Day 14: 400 emails
    }

    @classmethod
    def get_daily_count(cls, day: int) -> int:
        """Get number of emails to send on given warm-up day."""
        if day <= 0:
            return 0
        if day > 14:
            return 500  # Max after warm-up
        return cls.SCHEDULE.get(day, 50)


def generate_warmup_email() -> Dict[str, str]:
    """Generate a random warm-up email."""
    subject = random.choice(WARMUP_SUBJECTS)
    body = random.choice(WARMUP_BODIES)
    receiver = random.choice(WARMUP_RECEIVERS)
    name = random.choice(["Alex", "Sam", "Jordan", "Casey", "Morgan", "Taylor"])
    return {
        "to": receiver,
        "subject": subject,
        "body": body.format(name=name),
    }


async def get_warmup_day(db: AsyncSession, smtp_config_id: int) -> int:
    """Calculate current warm-up day based on first email sent."""
    result = await db.execute(
        select(EmailEvent.sent_at)
        .where(EmailEvent.smtp_config_id == smtp_config_id)
        .where(EmailEvent.is_warmup == True)
        .order_by(EmailEvent.sent_at.asc())
        .limit(1)
    )
    first_sent = result.scalar_one_or_none()
    if not first_sent:
        return 1
    delta = datetime.now(timezone.utc) - first_sent
    return delta.days + 1


async def send_warmup_batch(db: AsyncSession, smtp_config_id: int) -> Dict:
    """Send a batch of warm-up emails for the given SMTP config."""
    from app.services.email_service import get_email_provider

    # Get SMTP config
    smtp_config = await db.get(SMTPConfig, smtp_config_id)
    if not smtp_config or not smtp_config.is_active:
        return {"sent": 0, "reason": "SMTP config not found or inactive"}

    # Get warm-up day and count
    day = await get_warmup_day(db, smtp_config_id)
    daily_count = WarmupSchedule.get_daily_count(day)

    # Check how many warm-up emails sent today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(EmailEvent)
        .where(EmailEvent.smtp_config_id == smtp_config_id)
        .where(EmailEvent.is_warmup == True)
        .where(EmailEvent.sent_at >= today_start)
    )
    sent_today = len(result.scalars().all())

    remaining = daily_count - sent_today
    if remaining <= 0:
        return {"sent": 0, "reason": f"Warm-up complete for today (day {day}, {daily_count} emails)"}

    # Send warm-up emails
    provider = get_email_provider(smtp_config.provider, {
        "api_key": smtp_config.api_key,
        "smtp_host": smtp_config.smtp_host,
        "smtp_port": smtp_config.smtp_port,
        "smtp_username": smtp_config.smtp_username,
        "smtp_password": smtp_config.smtp_password,
        "smtp_use_tls": smtp_config.smtp_use_tls,
    })

    sent_count = 0
    for _ in range(min(remaining, 10)):  # Max 10 per batch
        email_data = generate_warmup_email()
        tracking_id = str(uuid.uuid4())

        try:
            result = await provider.send(
                to=email_data["to"],
                subject=email_data["subject"],
                html=email_data["body"],
                text="",
                from_email=smtp_config.from_email,
                from_name=smtp_config.from_name,
                tracking_id=tracking_id,
            )
            if result.get("success"):
                event = EmailEvent(
                    campaign_id=0,  # No campaign — warm-up
                    lead_id=0,
                    recipient_email=email_data["to"],
                    subject=email_data["subject"],
                    body_html=email_data["body"],
                    tracking_id=tracking_id,
                    status="sent",
                    sent_at=datetime.now(timezone.utc),
                    is_warmup=True,
                    smtp_config_id=smtp_config_id,
                )
                db.add(event)
                sent_count += 1
        except Exception as e:
            logger.error(f"Warm-up send failed: {e}")

    await db.commit()
    return {
        "sent": sent_count,
        "day": day,
        "daily_target": daily_count,
        "total_sent_today": sent_today + sent_count,
    }
