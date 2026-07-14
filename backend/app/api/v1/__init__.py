"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, leads, campaigns, tracking, dashboard, billing, warmup, ab_test

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(leads.router)
router.include_router(campaigns.router)
router.include_router(tracking.router)
router.include_router(dashboard.router)
router.include_router(billing.router)
router.include_router(warmup.router)
router.include_router(ab_test.router)
