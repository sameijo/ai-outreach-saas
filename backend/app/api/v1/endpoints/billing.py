"""Stripe billing and subscription management."""

import logging

try:
    import stripe
    HAS_STRIPE = True
except ImportError:
    stripe = None
    HAS_STRIPE = False
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/billing", tags=["billing"])

# Configure Stripe
if HAS_STRIPE:
    stripe.api_key = settings.stripe_secret_key if hasattr(settings, 'stripe_secret_key') else ""

# ── Plans ─────────────────────────────────────────────────
PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "credits": 100,
        "leads_per_search": 10,
        "campaigns": 2,
        "features": ["Basic lead search", "CSV upload", "SMTP sending"],
    },
    "starter": {
        "name": "Starter",
        "price": 49,
        "stripe_price_id": "price_starter_monthly",
        "credits": 2000,
        "leads_per_search": 50,
        "campaigns": 10,
        "features": ["Apollo + Hunter search", "AI personalization", "SendGrid/SES", "Basic analytics"],
    },
    "pro": {
        "name": "Pro",
        "price": 149,
        "stripe_price_id": "price_pro_monthly",
        "credits": 10000,
        "leads_per_search": 200,
        "campaigns": 50,
        "features": ["Everything in Starter", "A/B testing", "Follow-up sequences", "Priority support", "API access"],
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 499,
        "stripe_price_id": "price_enterprise_monthly",
        "credits": 50000,
        "leads_per_search": 1000,
        "campaigns": -1,  # unlimited
        "features": ["Everything in Pro", "Dedicated IP", "Custom integrations", "Account manager"],
    },
}


@router.get("/plans")
async def get_plans():
    """List all available plans."""
    return {"plans": PLANS}


@router.get("/subscription")
async def get_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's subscription details."""
    plan = PLANS.get(user.plan, PLANS["free"])
    return {
        "plan": user.plan,
        "plan_details": plan,
        "credits_remaining": user.credits_remaining,
        "stripe_customer_id": getattr(user, 'stripe_customer_id', None),
        "stripe_subscription_id": getattr(user, 'stripe_subscription_id', None),
    }


@router.post("/checkout")
async def create_checkout(
    plan: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe checkout session for plan upgrade."""
    if plan not in PLANS or plan == "free":
        raise HTTPException(status_code=400, detail="Invalid plan")

    plan_data = PLANS[plan]
    price_id = plan_data.get("stripe_price_id")

    if not stripe.api_key:
        # Demo mode — just upgrade directly
        user.plan = plan
        user.credits_remaining = plan_data["credits"]
        await db.commit()
        return {
            "mode": "demo",
            "plan": plan,
            "message": f"Upgraded to {plan} plan (demo mode — no Stripe configured)",
        }

    try:
        # Create or get Stripe customer
        customer_id = getattr(user, 'stripe_customer_id', None)
        if not customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={"user_id": str(user.id)},
            )
            customer_id = customer.id
            user.stripe_customer_id = customer_id

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.allowed_origins.split(',')[0]}/settings?success=true",
            cancel_url=f"{settings.allowed_origins.split(',')[0]}/settings?canceled=true",
            metadata={"user_id": str(user.id), "plan": plan},
        )

        await db.commit()
        return {"checkout_url": session.url, "session_id": session.id}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = getattr(settings, 'stripe_webhook_secret', '')

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            import json
            event = json.loads(payload)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook")

    event_type = event.get("type") if isinstance(event, dict) else event.type

    if event_type == "checkout.session.completed":
        session = event["data"]["object"] if isinstance(event, dict) else event.data.object
        user_id = int(session["metadata"]["user_id"])
        plan = session["metadata"]["plan"]

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.plan = plan
            user.credits_remaining = PLANS[plan]["credits"]
            user.stripe_subscription_id = session.get("subscription")
            await db.commit()
            logger.info(f"User {user_id} upgraded to {plan}")

    elif event_type == "customer.subscription.deleted":
        sub = event["data"]["object"] if isinstance(event, dict) else event.data.object
        # Downgrade to free
        result = await db.execute(select(User).where(User.stripe_subscription_id == sub["id"]))
        user = result.scalar_one_or_none()
        if user:
            user.plan = "free"
            user.credits_remaining = PLANS["free"]["credits"]
            await db.commit()

    elif event_type == "invoice.payment_failed":
        logger.warning("Payment failed — notify user")

    return {"status": "ok"}


@router.post("/cancel")
async def cancel_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel current subscription."""
    sub_id = getattr(user, 'stripe_subscription_id', None)
    if sub_id and stripe.api_key:
        try:
            stripe.Subscription.delete(sub_id)
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    user.plan = "free"
    user.stripe_subscription_id = None
    await db.commit()
    return {"detail": "Subscription canceled. Downgraded to free plan."}
