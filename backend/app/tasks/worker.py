"""Celery worker configuration — optional, only needed with Redis."""

import logging

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    from app.core.config import get_settings

    settings = get_settings()

    worker = Celery(
        "outreach",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )

    worker.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        beat_schedule={
            "send-campaign-batches": {
                "task": "app.tasks.campaign_tasks.send_campaign_batch",
                "interval": 60,
            },
        },
    )
except ImportError:
    logger.warning("Celery not installed — background scheduling disabled")
    worker = None
except Exception as e:
    logger.warning(f"Celery init failed: {e} — background scheduling disabled")
    worker = None
