"""Email tracking endpoints — open pixel, click redirect, unsubscribe."""

import base64
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.database import get_db
from app.core.config import get_settings
from app.models.campaign import EmailEvent, Campaign
from app.models.lead import Lead

router = APIRouter(prefix="/track", tags=["tracking"])
settings = get_settings()

# 1x1 transparent GIF
PIXEL_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


@router.get("/open/{tracking_id}")
async def track_open(tracking_id: str, db: AsyncSession = Depends(get_db)):
    """Track email open via invisible pixel."""
    result = await db.execute(
        select(EmailEvent).where(EmailEvent.tracking_id == tracking_id)
    )
    event = result.scalar_one_or_none()

    if event and event.status not in ("opened", "clicked", "replied"):
        event.status = "opened"
        event.opened_at = datetime.now(timezone.utc)
        event.open_count += 1

        # Update campaign stats
        campaign = await db.get(Campaign, event.campaign_id)
        if campaign:
            campaign.emails_opened += 1

        await db.commit()
    elif event:
        event.open_count += 1
        await db.commit()

    return Response(content=PIXEL_GIF, media_type="image/gif")


@router.get("/click/{tracking_id}")
async def track_click(
    tracking_id: str,
    url: str,
    db: AsyncSession = Depends(get_db),
):
    """Track link click and redirect to destination."""
    result = await db.execute(
        select(EmailEvent).where(EmailEvent.tracking_id == tracking_id)
    )
    event = result.scalar_one_or_none()

    if event:
        if event.status not in ("clicked", "replied"):
            event.status = "clicked"
            event.clicked_at = datetime.now(timezone.utc)
            event.click_count += 1

            # Update campaign stats
            campaign = await db.get(Campaign, event.campaign_id)
            if campaign:
                campaign.emails_clicked += 1
        else:
            event.click_count += 1

        clicked_urls = event.clicked_urls or []
        clicked_urls.append({"url": url, "timestamp": datetime.now(timezone.utc).isoformat()})
        event.clicked_urls = clicked_urls

        await db.commit()

    return RedirectResponse(url=url, status_code=302)


@router.get("/unsubscribe/{tracking_id}")
async def track_unsubscribe(tracking_id: str, db: AsyncSession = Depends(get_db)):
    """Handle unsubscribe request."""
    result = await db.execute(
        select(EmailEvent).where(EmailEvent.tracking_id == tracking_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Invalid unsubscribe link")

    # Mark lead as unsubscribed
    lead = await db.get(Lead, event.lead_id)
    if lead:
        lead.is_unsubscribed = True

    # Update event
    event.status = "unsubscribed"

    # Update campaign
    campaign = await db.get(Campaign, event.campaign_id)
    # Note: we don't decrement sent count, just mark as unsubscribed

    await db.commit()

    return {"detail": "You have been unsubscribed successfully."}


@router.post("/webhook/sendgrid")
async def sendgrid_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle SendGrid event webhook."""
    events = await request.json()
    for event_data in events:
        tracking_id = event_data.get("tracking_id", "")
        event_type = event_data.get("event", "")

        if not tracking_id:
            continue

        result = await db.execute(
            select(EmailEvent).where(EmailEvent.tracking_id == tracking_id)
        )
        event = result.scalar_one_or_none()
        if not event:
            continue

        campaign = await db.get(Campaign, event.campaign_id)

        if event_type == "bounce":
            event.status = "bounced"
            event.bounced_at = datetime.now(timezone.utc)
            event.bounce_reason = event_data.get("reason", "")
            if campaign:
                campaign.emails_bounced += 1
            # Mark lead
            lead = await db.get(Lead, event.lead_id)
            if lead:
                lead.is_bounced = True

        elif event_type == "dropped":
            event.status = "failed"
            if campaign:
                campaign.emails_failed += 1

        elif event_type == "reply":
            event.status = "replied"
            event.replied_at = datetime.now(timezone.utc)
            if campaign:
                campaign.emails_replied += 1
            lead = await db.get(Lead, event.lead_id)
            if lead:
                lead.is_replied = True

    await db.commit()
    return {"processed": len(events)}


@router.post("/webhook/ses")
async def ses_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Amazon SES notification webhook."""
    # SES sends SNS notifications — simplified handler
    body = await request.json()
    # Process bounce/complaint/delivery notifications
    return {"status": "ok"}
