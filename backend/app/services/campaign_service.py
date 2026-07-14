"""Campaign orchestration service."""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models import Campaign, EmailEvent, Lead, LeadList, SMTPConfig
from app.services.email_service import get_email_provider, inject_tracking
from app.services.ai_service import ai_service
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CampaignService:
    """Orchestrate campaign execution: personalize → send → track."""

    async def start_campaign(self, db: AsyncSession, campaign_id: int) -> Dict:
        """Initialize a campaign — create EmailEvent entries for all leads."""
        campaign = await db.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        if campaign.status not in ("draft", "paused"):
            raise ValueError(f"Cannot start campaign in '{campaign.status}' status")

        # Get leads
        result = await db.execute(
            select(Lead).where(
                Lead.lead_list_id == campaign.lead_list_id,
                Lead.is_contacted == False,
                Lead.is_unsubscribed == False,
            )
        )
        leads = result.scalars().all()

        if not leads:
            raise ValueError("No eligible leads found")

        # Create email events
        events_created = 0
        for lead in leads:
            tracking_id = str(uuid.uuid4())
            event = EmailEvent(
                campaign_id=campaign.id,
                lead_id=lead.id,
                recipient_email=lead.email,
                subject=campaign.subject,
                body_html=campaign.body_html,
                tracking_id=tracking_id,
                status="queued",
                follow_up_step=0,
            )
            db.add(event)
            events_created += 1

        # Update campaign
        campaign.status = "active"
        campaign.started_at = datetime.now(timezone.utc)
        campaign.total_leads = events_created

        await db.commit()
        logger.info(f"Campaign {campaign.id} started with {events_created} emails queued")
        return {"campaign_id": campaign.id, "emails_queued": events_created}

    async def send_batch(self, db: AsyncSession, campaign_id: int, batch_size: int = 10) -> Dict:
        """Send a batch of queued emails for a campaign."""
        campaign = await db.get(Campaign, campaign_id)
        if not campaign or campaign.status != "active":
            return {"sent": 0, "reason": "Campaign not active"}

        # Get SMTP config
        smtp_config = None
        if campaign.smtp_config_id:
            smtp_config = await db.get(SMTPConfig, campaign.smtp_config_id)
        if not smtp_config:
            result = await db.execute(
                select(SMTPConfig).where(SMTPConfig.user_id == campaign.user_id, SMTPConfig.is_default == True)
            )
            smtp_config = result.scalar_one_or_none()
        if not smtp_config:
            return {"sent": 0, "reason": "No SMTP configuration found"}

        # Get queued emails
        result = await db.execute(
            select(EmailEvent).where(
                EmailEvent.campaign_id == campaign_id,
                EmailEvent.status == "queued",
            ).limit(batch_size)
        )
        events = result.scalars().all()

        if not events:
            # Check if campaign is complete
            remaining = await db.execute(
                select(func.count()).select_from(EmailEvent).where(
                    EmailEvent.campaign_id == campaign_id,
                    EmailEvent.status.in_(["queued", "sending"]),
                )
            )
            if remaining.scalar() == 0:
                campaign.status = "completed"
                campaign.completed_at = datetime.now(timezone.utc)
                await db.commit()
            return {"sent": 0, "reason": "No more emails to send"}

        # Get provider
        provider = get_email_provider(smtp_config.provider, {
            "api_key": smtp_config.api_key,
            "smtp_host": smtp_config.smtp_host,
            "smtp_port": smtp_config.smtp_port,
            "smtp_username": smtp_config.smtp_username,
            "smtp_password": smtp_config.smtp_password,
            "smtp_use_tls": smtp_config.smtp_use_tls,
        })

        sent_count = 0
        for event in events:
            # Get lead for personalization
            lead = await db.get(Lead, event.lead_id)
            if not lead or lead.is_unsubscribed:
                event.status = "skipped"
                continue

            # AI personalization
            body_html = event.body_html
            if campaign.personalize_with_ai and not lead.ai_intro:
                try:
                    lead.ai_intro = await ai_service.generate_personalized_intro(
                        first_name=lead.first_name,
                        last_name=lead.last_name,
                        job_title=lead.job_title,
                        company=lead.company,
                        industry=lead.industry,
                        company_website=lead.company_website,
                        tone=campaign.ai_tone,
                    )
                    lead.ai_enriched = True
                except Exception as e:
                    logger.warning(f"AI personalization failed for {lead.email}: {e}")

            # Replace template variables
            body_html = self._render_template(body_html, lead, campaign)
            subject = self._render_template(event.subject, lead, campaign)

            # Inject tracking
            body_html = inject_tracking(body_html, event.tracking_id, settings.tracking_domain)

            # Send
            event.status = "sending"
            try:
                result = await provider.send(
                    to=event.recipient_email,
                    subject=subject,
                    html=body_html,
                    text="",
                    from_email=smtp_config.from_email,
                    from_name=smtp_config.from_name,
                    reply_to=smtp_config.reply_to,
                    tracking_id=event.tracking_id,
                )
                if result["success"]:
                    event.status = "sent"
                    event.sent_at = datetime.now(timezone.utc)
                    event.message_id = result.get("message_id", "")
                    event.subject = subject
                    event.body_html = body_html
                    lead.is_contacted = True
                    campaign.emails_sent += 1
                    sent_count += 1
                else:
                    event.status = "failed"
                    campaign.emails_failed += 1
            except Exception as e:
                logger.error(f"Send failed for {event.recipient_email}: {e}")
                event.status = "failed"
                campaign.emails_failed += 1

        await db.commit()
        return {"sent": sent_count, "campaign_id": campaign_id}

    def _render_template(self, template: str, lead: Lead, campaign: Campaign) -> str:
        """Replace template variables with lead data."""
        replacements = {
            "{{first_name}}": lead.first_name or "",
            "{{last_name}}": lead.last_name or "",
            "{{full_name}}": f"{lead.first_name} {lead.last_name}".strip(),
            "{{email}}": lead.email or "",
            "{{company}}": lead.company or "",
            "{{job_title}}": lead.job_title or "",
            "{{industry}}": lead.industry or "",
            "{{website}}": lead.company_website or "",
            "{{ai_intro}}": lead.ai_intro or "",
            "$first_name": lead.first_name or "",
            "$last_name": lead.last_name or "",
            "$company": lead.company or "",
            "$job_title": lead.job_title or "",
            "$ai_intro": lead.ai_intro or "",
        }
        for key, value in replacements.items():
            template = template.replace(key, value)
        return template

    async def get_campaign_stats(self, db: AsyncSession, campaign_id: int) -> Dict:
        """Get detailed campaign statistics."""
        campaign = await db.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        total = campaign.total_leads or 1
        return {
            "total_leads": campaign.total_leads,
            "emails_sent": campaign.emails_sent,
            "emails_opened": campaign.emails_opened,
            "open_rate": round(campaign.emails_opened / total * 100, 1),
            "emails_clicked": campaign.emails_clicked,
            "click_rate": round(campaign.emails_clicked / total * 100, 1),
            "emails_replied": campaign.emails_replied,
            "reply_rate": round(campaign.emails_replied / total * 100, 1),
            "emails_bounced": campaign.emails_bounced,
            "bounce_rate": round(campaign.emails_bounced / total * 100, 1),
            "emails_failed": campaign.emails_failed,
        }


campaign_service = CampaignService()
