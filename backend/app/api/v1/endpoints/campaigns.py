"""Campaign management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.campaign import Campaign, SMTPConfig, EmailEvent
from app.schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignStats, SMTPConfigCreate, SMTPConfigResponse, EmailEventResponse,
)
from app.services.campaign_service import campaign_service
from app.tasks.campaign_tasks import send_campaign_batch

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# ── Campaigns ─────────────────────────────────────────────

@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[str] = None,
    skip: int = 0, limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Campaign).where(Campaign.user_id == user.id)
    if status:
        query = query.where(Campaign.status == status)
    query = query.order_by(Campaign.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    data: CampaignCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    campaign = Campaign(
        user_id=user.id,
        name=data.name,
        lead_list_id=data.lead_list_id,
        smtp_config_id=data.smtp_config_id,
        subject=data.subject,
        body_html=data.body_html,
        body_text=data.body_text,
        follow_ups=[f.model_dump() for f in data.follow_ups],
        send_rate_per_hour=data.send_rate_per_hour,
        send_rate_per_day=data.send_rate_per_day,
        send_window_start=data.send_window_start,
        send_window_end=data.send_window_end,
        timezone=data.timezone,
        personalize_with_ai=data.personalize_with_ai,
        ai_tone=data.ai_tone,
        scheduled_at=data.scheduled_at,
    )
    db.add(campaign)
    await db.commit()
    return campaign


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)

    await db.commit()
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status == "active":
        raise HTTPException(status_code=400, detail="Pause campaign before deleting")
    await db.delete(campaign)
    return {"detail": "Deleted"}


# ── Campaign Actions ──────────────────────────────────────

@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await campaign_service.start_campaign(db, campaign_id)
    return result


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = "paused"
    await db.commit()
    return {"detail": "Paused"}


@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "paused":
        raise HTTPException(status_code=400, detail="Can only resume paused campaigns")
    campaign.status = "active"
    await db.commit()
    return {"detail": "Resumed"}


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await campaign_service.get_campaign_stats(db, campaign_id)


@router.get("/{campaign_id}/events", response_model=List[EmailEventResponse])
async def get_campaign_events(
    campaign_id: int,
    status: Optional[str] = None,
    skip: int = 0, limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(EmailEvent).where(EmailEvent.campaign_id == campaign_id)
    if status:
        query = query.where(EmailEvent.status == status)
    query = query.order_by(EmailEvent.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{campaign_id}/send-batch")
async def trigger_send_batch(
    campaign_id: int,
    batch_size: int = Query(default=10, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a batch send."""
    task = send_campaign_batch.delay(campaign_id, batch_size)
    return {"task_id": task.id, "batch_size": batch_size}


# ── SMTP Configs ──────────────────────────────────────────

@router.get("/smtp-configs/list", response_model=List[SMTPConfigResponse])
async def list_smtp_configs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SMTPConfig).where(SMTPConfig.user_id == user.id).order_by(SMTPConfig.created_at.desc())
    )
    return result.scalars().all()


@router.post("/smtp-configs", response_model=SMTPConfigResponse, status_code=201)
async def create_smtp_config(
    data: SMTPConfigCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = SMTPConfig(user_id=user.id, **data.model_dump())
    db.add(config)
    await db.commit()
    return config


@router.put("/smtp-configs/{config_id}", response_model=SMTPConfigResponse)
async def update_smtp_config(
    config_id: int,
    data: SMTPConfigCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SMTPConfig).where(SMTPConfig.id == config_id, SMTPConfig.user_id == user.id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="SMTP config not found")
    for field, value in data.model_dump().items():
        setattr(config, field, value)
    await db.commit()
    return config


@router.delete("/smtp-configs/{config_id}")
async def delete_smtp_config(
    config_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SMTPConfig).where(SMTPConfig.id == config_id, SMTPConfig.user_id == user.id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="SMTP config not found")
    await db.delete(config)
    return {"detail": "Deleted"}
