"""AI content generation service — personalized email intros using OpenAI/GPT."""

import json
import logging
from typing import Dict, Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are an expert cold email copywriter. Your job is to write a hyper-personalized opening line for a cold email.

Rules:
- Reference something specific about the person (their role, company, recent work, industry trend)
- Keep it 1-2 sentences max
- Sound natural, not salesy
- Match the requested tone
- Do NOT include "Hi [Name]" — just the personalized hook after the greeting
- Do NOT use placeholder brackets — use the actual provided data

Output ONLY the personalized opening line, nothing else."""

TONE_INSTRUCTIONS = {
    "professional": "Write in a professional, business-appropriate tone.",
    "casual": "Write in a friendly, conversational tone — like emailing a colleague.",
    "persuasive": "Write in a compelling, benefit-driven tone that creates curiosity.",
}


class AIService:
    """Generate personalized email content using OpenAI."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_personalized_intro(
        self,
        first_name: str,
        last_name: str,
        job_title: str,
        company: str,
        industry: str,
        company_website: str = "",
        linkedin_snippet: str = "",
        tone: str = "professional",
    ) -> str:
        """Generate a personalized opening line for a cold email."""
        if not self.client:
            return f"Hi {first_name}, I came across {company} and was impressed by your work in {industry}."

        context_parts = []
        if first_name:
            context_parts.append(f"Name: {first_name} {last_name}")
        if job_title:
            context_parts.append(f"Job Title: {job_title}")
        if company:
            context_part = f"Company: {company}"
            if industry:
                context_part += f" (Industry: {industry})"
            context_parts.append(context_part)
        if company_website:
            context_parts.append(f"Website: {company_website}")
        if linkedin_snippet:
            context_parts.append(f"Recent LinkedIn activity: {linkedin_snippet}")

        context = "\n".join(context_parts)
        tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["professional"])

        user_prompt = f"""Generate a personalized cold email opening line for:

{context}

Tone: {tone_instruction}

Write ONLY the personalized hook (1-2 sentences). Start naturally, as if continuing after "Hi {first_name},"."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=150,
                temperature=0.8,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return f"Hi {first_name}, I noticed {company}'s work in {industry} and wanted to reach out."

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_full_email(
        self,
        lead_info: Dict,
        product_description: str,
        tone: str = "professional",
        cta: str = "",
    ) -> Dict[str, str]:
        """Generate a complete personalized cold email."""
        if not self.client:
            return {
                "subject": f"Quick question, {lead_info.get('first_name', '')}",
                "body_html": f"<p>Hi {lead_info.get('first_name', '')},</p><p>I'd love to connect.</p>",
                "body_text": f"Hi {lead_info.get('first_name', '')},\n\nI'd love to connect.",
            }

        tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["professional"])

        prompt = f"""Write a cold email for:

Lead: {json.dumps(lead_info, indent=2)}

Product/Service: {product_description}
Tone: {tone_instruction}
CTA: {cta or 'Schedule a quick call'}

Output JSON with keys: subject, body_html, body_text
- subject: compelling subject line (max 60 chars)
- body_html: full HTML email with proper formatting
- body_text: plain text version
- Keep email under 150 words
- Include a clear CTA
- Do NOT include unsubscribe link (added automatically)"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert cold email copywriter. Output valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.7,
            )
            content = response.choices[0].message.content.strip()
            # Handle markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Full email generation failed: {e}")
            return {
                "subject": f"Connecting with {lead_info.get('company', 'you')}",
                "body_html": f"<p>Hi {lead_info.get('first_name', '')},</p><p>I'd love to discuss how we can help.</p>",
                "body_text": f"Hi {lead_info.get('first_name', '')},\n\nI'd love to discuss how we can help.",
            }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_subject_variants(self, base_subject: str, count: int = 5) -> list[str]:
        """Generate subject line variants for A/B testing."""
        if not self.client:
            return [base_subject]

        prompt = f"""Generate {count} variants of this email subject line: "{base_subject}"

Output a JSON array of strings. Each variant should be under 60 chars and test a different angle (curiosity, benefit, question, urgency, personalization)."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.9,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except Exception:
            return [base_subject]


# Scrape company website for context
async def scrape_website_context(url: str) -> str:
    """Scrape a company website for context to feed into AI."""
    import httpx
    from bs4 import BeautifulSoup

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        # Limit context
        return text[:2000]
    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")
        return ""


ai_service = AIService()
