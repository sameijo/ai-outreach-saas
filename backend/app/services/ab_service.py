"""A/B testing service for email subject lines and content."""

import random
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.campaign import Campaign, EmailEvent

logger = logging.getLogger(__name__)


class ABTestService:
    """Manage A/B tests for campaigns."""

    async def create_ab_test(
        self,
        db: AsyncSession,
        campaign_id: int,
        variants: List[Dict],
        test_percentage: int = 20,
        winner_metric: str = "open_rate",  # open_rate, click_rate, reply_rate
    ) -> Dict:
        """
        Create an A/B test for a campaign.
        
        variants: [
            {"name": "Variant A", "subject": "...", "body_html": "..."},
            {"name": "Variant B", "subject": "...", "body_html": "..."},
        ]
        test_percentage: % of leads to use for testing (rest gets winner)
        winner_metric: which metric decides the winner
        """
        campaign = await db.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        import json

        # Store A/B test config in campaign metadata
        ab_config = {
            "variants": variants,
            "test_percentage": test_percentage,
            "winner_metric": winner_metric,
            "status": "testing",  # testing, winner_selected
            "winner_variant": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        campaign.ab_test_config = json.dumps(ab_config)
        await db.commit()

        return {
            "campaign_id": campaign_id,
            "variants": len(variants),
            "test_percentage": test_percentage,
            "winner_metric": winner_metric,
            "status": "testing",
        }

    async def get_variant_for_lead(
        self,
        db: AsyncSession,
        campaign_id: int,
        lead_index: int,
    ) -> Optional[Dict]:
        """Get which variant a lead should receive."""
        campaign = await db.get(Campaign, campaign_id)
        if not campaign or not campaign.ab_test_config:
            return None

        import json
        config = json.loads(campaign.ab_test_config)
        variants = config["variants"]

        if config["status"] == "winner_selected" and config["winner_variant"] is not None:
            return variants[config["winner_variant"]]

        # Rotate variants evenly
        variant_index = lead_index % len(variants)
        return variants[variant_index]

    async def analyze_results(
        self,
        db: AsyncSession,
        campaign_id: int,
    ) -> Dict:
        """Analyze A/B test results and determine winner."""
        campaign = await db.get(Campaign, campaign_id)
        if not campaign or not campaign.ab_test_config:
            raise ValueError("No A/B test found for this campaign")

        import json
        config = json.loads(campaign.ab_test_config)
        variants = config["variants"]

        results = []
        for i, variant in enumerate(variants):
            # Count events for this variant
            events = await db.execute(
                select(EmailEvent).where(
                    EmailEvent.campaign_id == campaign_id,
                    EmailEvent.follow_up_step == 0,  # Only initial emails
                )
            )
            all_events = events.scalars().all()

            # Simulate variant assignment (same logic as get_variant_for_lead)
            variant_events = [e for j, e in enumerate(all_events) if j % len(variants) == i]

            total = len(variant_events)
            if total == 0:
                results.append({
                    "variant": variant.get("name", f"Variant {i}"),
                    "subject": variant.get("subject", ""),
                    "total_sent": 0,
                    "open_rate": 0,
                    "click_rate": 0,
                    "reply_rate": 0,
                })
                continue

            opened = sum(1 for e in variant_events if e.status in ("opened", "clicked", "replied"))
            clicked = sum(1 for e in variant_events if e.status in ("clicked", "replied"))
            replied = sum(1 for e in variant_events if e.status == "replied")

            results.append({
                "variant": variant.get("name", f"Variant {i}"),
                "subject": variant.get("subject", ""),
                "total_sent": total,
                "open_rate": round(opened / total * 100, 1),
                "click_rate": round(clicked / total * 100, 1),
                "reply_rate": round(replied / total * 100, 1),
                "score": opened if config["winner_metric"] == "open_rate" else clicked if config["winner_metric"] == "click_rate" else replied,
            })

        # Determine winner
        winner_idx = max(range(len(results)), key=lambda i: results[i]["score"])
        winner = results[winner_idx]

        return {
            "campaign_id": campaign_id,
            "variants": results,
            "winner": winner,
            "winner_metric": config["winner_metric"],
            "status": config["status"],
        }

    async def select_winner(
        self,
        db: AsyncSession,
        campaign_id: int,
        variant_index: int,
    ) -> Dict:
        """Manually or automatically select a winner variant."""
        campaign = await db.get(Campaign, campaign_id)
        if not campaign or not campaign.ab_test_config:
            raise ValueError("No A/B test found")

        import json
        config = json.loads(campaign.ab_test_config)
        config["status"] = "winner_selected"
        config["winner_variant"] = variant_index
        campaign.ab_test_config = json.dumps(config)
        await db.commit()

        return {
            "campaign_id": campaign_id,
            "winner_variant": variant_index,
            "variant": config["variants"][variant_index],
            "status": "winner_selected",
        }

    async def auto_select_winner(
        self,
        db: AsyncSession,
        campaign_id: int,
        min_sample_size: int = 20,
    ) -> Dict:
        """Automatically select winner based on performance."""
        analysis = await self.analyze_results(db, campaign_id)

        if analysis["status"] == "winner_selected":
            return analysis

        # Check if enough data
        total_sent = sum(v["total_sent"] for v in analysis["variants"])
        if total_sent < min_sample_size:
            return {**analysis, "message": f"Need {min_sample_size - total_sent} more sends before auto-selecting"}

        # Find winner
        winner_idx = max(
            range(len(analysis["variants"])),
            key=lambda i: analysis["variants"][i]["score"]
        )

        return await self.select_winner(db, campaign_id, winner_idx)


ab_service = ABTestService()
