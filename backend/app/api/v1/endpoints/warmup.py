"""Email warm-up endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.campaign import SMTPConfig
from app.services.warmup_service import send_warmup_batch, get_warmup_day, WarmupSchedule

router = APIRouter(prefix="/warmup", tags=["warmup"])


@router.post("/start/{smtp_config_id}")
async def start_warmup(
    smtp_config_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start warm-up for an SMTP config."""
    result = await db.execute(
        select(SMTPConfig).where(SMTPConfig.id == smtp_config_id, SMTPConfig.user_id == user.id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="SMTP config not found")

    batch_result = await send_warmup_batch(db, smtp_config_id)
    return batch_result


@router.get("/status/{smtp_config_id}")
async def warmup_status(
    smtp_config_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get warm-up status for an SMTP config."""
    result = await db.execute(
        select(SMTPConfig).where(SMTPConfig.id == smtp_config_id, SMTPConfig.user_id == user.id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="SMTP config not found")

    day = await get_warmup_day(db, smtp_config_id)
    daily_target = WarmupSchedule.get_daily_count(day)

    return {
        "smtp_config_id": smtp_config_id,
        "warmup_day": day,
        "daily_target": daily_target,
        "schedule": {str(d): WarmupSchedule.get_daily_count(d) for d in range(1, 15)},
        "status": "active" if day > 0 else "not_started",
    }
