"""Dashboard and analytics endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.campaign import Campaign, EmailEvent
from app.models.lead import Lead, LeadList

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
async def get_overview(
    days: int = Query(default=30, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard overview stats."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total leads
    leads_result = await db.execute(
        select(func.count()).select_from(Lead)
        .join(LeadList, Lead.lead_list_id == LeadList.id)
        .where(LeadList.user_id == user.id)
    )
    total_leads = leads_result.scalar() or 0

    # Campaign stats
    campaigns_result = await db.execute(
        select(
            func.count(Campaign.id).label("total_campaigns"),
            func.sum(Campaign.emails_sent).label("emails_sent"),
            func.sum(Campaign.emails_opened).label("emails_opened"),
            func.sum(Campaign.emails_clicked).label("emails_clicked"),
            func.sum(Campaign.emails_replied).label("emails_replied"),
            func.sum(Campaign.emails_bounced).label("emails_bounced"),
            func.sum(Campaign.emails_failed).label("emails_failed"),
        ).where(Campaign.user_id == user.id)
    )
    stats = campaigns_result.one()

    emails_sent = int(stats.emails_sent or 0)
    emails_opened = int(stats.emails_opened or 0)
    emails_clicked = int(stats.emails_clicked or 0)
    emails_replied = int(stats.emails_replied or 0)
    emails_bounced = int(stats.emails_bounced or 0)

    return {
        "total_leads": total_leads,
        "total_campaigns": stats.total_campaigns or 0,
        "active_campaigns": (await db.execute(
            select(func.count()).select_from(Campaign)
            .where(Campaign.user_id == user.id, Campaign.status == "active")
        )).scalar() or 0,
        "emails_sent": emails_sent,
        "emails_opened": emails_opened,
        "open_rate": round(emails_opened / max(emails_sent, 1) * 100, 1),
        "emails_clicked": emails_clicked,
        "click_rate": round(emails_clicked / max(emails_sent, 1) * 100, 1),
        "emails_replied": emails_replied,
        "reply_rate": round(emails_replied / max(emails_sent, 1) * 100, 1),
        "emails_bounced": emails_bounced,
        "bounce_rate": round(emails_bounced / max(emails_sent, 1) * 100, 1),
        "credits_remaining": user.credits_remaining,
    }


@router.get("/activity")
async def get_activity_chart(
    days: int = Query(default=30, le=90),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily email activity for chart."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(EmailEvent)
        .join(Campaign, EmailEvent.campaign_id == Campaign.id)
        .where(Campaign.user_id == user.id, EmailEvent.created_at >= since)
    )
    events = result.scalars().all()

    # Group by day
    daily = {}
    for event in events:
        day = event.created_at.strftime("%Y-%m-%d") if event.created_at else "unknown"
        if day not in daily:
            daily[day] = {"date": day, "sent": 0, "opened": 0, "clicked": 0, "replied": 0, "bounced": 0}
        if event.status in ("sent", "delivered", "opened", "clicked", "replied"):
            daily[day]["sent"] += 1
        if event.status in ("opened", "clicked", "replied"):
            daily[day]["opened"] += 1
        if event.status in ("clicked", "replied"):
            daily[day]["clicked"] += 1
        if event.status == "replied":
            daily[day]["replied"] += 1
        if event.status == "bounced":
            daily[day]["bounced"] += 1

    return sorted(daily.values(), key=lambda x: x["date"])


@router.get("/campaigns/summary")
async def get_campaigns_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary of all campaigns."""
    result = await db.execute(
        select(Campaign)
        .where(Campaign.user_id == user.id)
        .order_by(Campaign.created_at.desc())
        .limit(20)
    )
    campaigns = result.scalars().all()

    summaries = []
    for c in campaigns:
        sent = c.emails_sent or 1
        summaries.append({
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "total_leads": c.total_leads,
            "emails_sent": c.emails_sent,
            "open_rate": round((c.emails_opened or 0) / sent * 100, 1),
            "click_rate": round((c.emails_clicked or 0) / sent * 100, 1),
            "reply_rate": round((c.emails_replied or 0) / sent * 100, 1),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return summaries


@router.get("/export/csv")
async def export_leads_csv(
    list_id: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export leads to CSV (returns JSON that frontend converts to CSV)."""
    query = select(Lead).join(LeadList, Lead.lead_list_id == LeadList.id).where(LeadList.user_id == user.id)
    if list_id:
        query = query.where(Lead.lead_list_id == list_id)

    result = await db.execute(query.order_by(Lead.id))
    leads = result.scalars().all()

    rows = []
    for lead in leads:
        rows.append({
            "email": lead.email,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "job_title": lead.job_title,
            "company": lead.company,
            "company_website": lead.company_website,
            "linkedin_url": lead.linkedin_url,
            "phone": lead.phone,
            "location": lead.location,
            "industry": lead.industry,
            "email_verified": lead.email_verified,
            "ai_intro": lead.ai_intro,
            "is_contacted": lead.is_contacted,
            "is_replied": lead.is_replied,
        })

    return {"data": rows, "total": len(rows)}
