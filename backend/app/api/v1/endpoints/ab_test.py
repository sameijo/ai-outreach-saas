"""A/B testing endpoints for campaigns."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.ab_service import ab_service

router = APIRouter(prefix="/ab-test", tags=["ab-testing"])


class ABVariant(BaseModel):
    name: str = "Variant"
    subject: str
    body_html: str


class ABTestCreate(BaseModel):
    campaign_id: int
    variants: List[ABVariant]
    test_percentage: int = 20
    winner_metric: str = "open_rate"


class WinnerSelect(BaseModel):
    campaign_id: int
    variant_index: int


@router.post("/create")
async def create_ab_test(
    data: ABTestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create A/B test with multiple subject/content variants."""
    result = await ab_service.create_ab_test(
        db=db,
        campaign_id=data.campaign_id,
        variants=[v.model_dump() for v in data.variants],
        test_percentage=data.test_percentage,
        winner_metric=data.winner_metric,
    )
    return result


@router.get("/results/{campaign_id}")
async def get_ab_results(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get A/B test results with performance metrics per variant."""
    return await ab_service.analyze_results(db, campaign_id)


@router.post("/select-winner")
async def select_winner(
    data: WinnerSelect,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually select the winning variant."""
    return await ab_service.select_winner(db, data.campaign_id, data.variant_index)


@router.post("/auto-winner/{campaign_id}")
async def auto_select_winner(
    campaign_id: int,
    min_sample: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-select winner based on performance metrics."""
    return await ab_service.auto_select_winner(db, campaign_id, min_sample)
