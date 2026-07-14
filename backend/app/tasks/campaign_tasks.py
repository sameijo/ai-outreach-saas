"""Campaign background tasks — works with or without Celery."""

import asyncio
import logging

logger = logging.getLogger(__name__)

# Try importing Celery; fall back to direct execution if unavailable
try:
    from celery import shared_task
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    logger.warning("Celery not installed — background tasks will run synchronously")

    # Stub decorator for when Celery isn't available
    def shared_task(*args, **kwargs):
        def decorator(func):
            func.delay = lambda *a, **kw: _run_sync(func, *a, **kw)
            func.apply_async = func.delay
            return func
        return decorator


def _run_sync(func, *args, **kwargs):
    """Run an async function synchronously when Celery isn't available."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're already in an async context — schedule and return a fake result
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, func(*args, **kwargs))
                result = future.result(timeout=60)
        else:
            result = loop.run_until_complete(func(*args, **kwargs))
    except RuntimeError:
        result = asyncio.run(func(*args, **kwargs))

    class FakeResult:
        def __init__(self, r):
            self._result = r
            self.id = "sync"
        def get(self, timeout=None):
            return self._result
    return FakeResult(result)


def run_async(coro):
    """Run async function in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result(timeout=120)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(name="app.tasks.campaign_tasks.send_campaign_batch")
def send_campaign_batch(campaign_id: int, batch_size: int = 10):
    """Send a batch of emails for a specific campaign."""
    async def _send():
        from app.core.database import async_session
        from app.services.campaign_service import campaign_service
        async with async_session() as db:
            result = await campaign_service.send_batch(db, campaign_id, batch_size)
            logger.info(f"Campaign {campaign_id} batch result: {result}")
            return result
    return run_async(_send())


@shared_task(name="app.tasks.campaign_tasks.enrich_leads_with_ai")
def enrich_leads_with_ai(lead_ids: list, tone: str = "professional"):
    """Enrich leads with AI-generated personalized intros."""
    async def _enrich():
        from app.core.database import async_session
        from app.models import Lead
        from app.services.ai_service import ai_service

        async with async_session() as db:
            for lead_id in lead_ids:
                lead = await db.get(Lead, lead_id)
                if not lead or lead.ai_enriched:
                    continue
                try:
                    intro = await ai_service.generate_personalized_intro(
                        first_name=lead.first_name,
                        last_name=lead.last_name,
                        job_title=lead.job_title,
                        company=lead.company,
                        industry=lead.industry,
                        company_website=lead.company_website,
                        tone=tone,
                    )
                    lead.ai_intro = intro
                    lead.ai_enriched = True
                    logger.info(f"Enriched lead {lead.email}")
                except Exception as e:
                    logger.error(f"Failed to enrich lead {lead.email}: {e}")

            await db.commit()
    return run_async(_enrich())


@shared_task(name="app.tasks.campaign_tasks.verify_leads")
def verify_leads(lead_ids: list):
    """Verify email addresses for a batch of leads."""
    async def _verify():
        from app.core.database import async_session
        from app.models import Lead
        from app.services.lead_service import EmailVerifier

        async with async_session() as db:
            verifier = EmailVerifier()
            for lead_id in lead_ids:
                lead = await db.get(Lead, lead_id)
                if not lead:
                    continue
                try:
                    result = await verifier.verify(lead.email)
                    lead.verification_status = result.get("status", "unknown")
                    lead.email_verified = result.get("status") == "valid"
                    logger.info(f"Verified {lead.email}: {result['status']}")
                except Exception as e:
                    logger.error(f"Verification failed for {lead.email}: {e}")

            await db.commit()
    return run_async(_verify())
