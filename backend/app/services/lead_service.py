"""Lead discovery service — Apollo.io and Hunter.io integrations."""

import httpx
import dns.resolver
import re
import json
import logging
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ApolloClient:
    """Apollo.io API integration for lead discovery."""

    BASE_URL = "https://api.apollo.io/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def search_people(self, query: str, page: int = 1, per_page: int = 25) -> List[Dict]:
        """Search for people matching query."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.BASE_URL}/mixed_people/search",
                headers=self.headers,
                json={
                    "api_key": self.api_key,
                    "q_keywords": query,
                    "page": page,
                    "per_page": per_page,
                    "person_seniorities": ["director", "vp", "c_level", "founder", "owner"],
                },
            )
            resp.raise_for_status()
            data = resp.json()

        leads = []
        for person in data.get("people", []):
            leads.append({
                "email": person.get("email", ""),
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "job_title": person.get("title", ""),
                "company": (person.get("organization") or {}).get("name", ""),
                "company_website": (person.get("organization") or {}).get("website_url", ""),
                "linkedin_url": person.get("linkedin_url", ""),
                "phone": person.get("phone_numbers", [{}])[0].get("sanitized_number", "") if person.get("phone_numbers") else "",
                "location": f"{person.get('city', '')}, {person.get('country', '')}".strip(", "),
                "industry": (person.get("organization") or {}).get("industry", ""),
                "company_size": (person.get("organization") or {}).get("estimated_num_employees", ""),
            })
        return leads

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_organization_info(self, domain: str) -> Dict:
        """Get company info by domain."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.BASE_URL}/organizations/enrich",
                headers=self.headers,
                json={"api_key": self.api_key, "domain": domain},
            )
            resp.raise_for_status()
            return resp.json().get("organization", {})


class HunterClient:
    """Hunter.io API integration for email discovery."""

    BASE_URL = "https://api.hunter.io/v2"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def domain_search(self, domain: str, limit: int = 25) -> List[Dict]:
        """Find emails associated with a domain."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.BASE_URL}/domain-search",
                params={"domain": domain, "api_key": self.api_key, "limit": limit},
            )
            resp.raise_for_status()
            data = resp.json()

        leads = []
        for email_data in data.get("data", {}).get("emails", []):
            leads.append({
                "email": email_data.get("value", ""),
                "first_name": email_data.get("first_name", ""),
                "last_name": email_data.get("last_name", ""),
                "job_title": email_data.get("position", ""),
                "company": data.get("data", {}).get("organization", ""),
                "company_website": f"https://{domain}",
                "linkedin_url": email_data.get("linkedin", ""),
                "phone": email_data.get("phone_number", ""),
                "location": "",
                "industry": "",
                "company_size": "",
            })
        return leads

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def email_finder(self, domain: str, first_name: str, last_name: str) -> Optional[Dict]:
        """Find a specific person's email."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.BASE_URL}/email-finder",
                params={
                    "domain": domain,
                    "first_name": first_name,
                    "last_name": last_name,
                    "api_key": self.api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                "email": data.get("email", ""),
                "confidence": data.get("confidence", 0),
                "position": data.get("position", ""),
            }


class EmailVerifier:
    """Email verification using DNS checks and API services."""

    DISPOSABLE_DOMAINS = {
        "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
        "yopmail.com", "sharklasers.com", "guerrillamailblock.com", "grr.la",
    }

    @staticmethod
    async def verify_with_hunter(email: str) -> Dict:
        """Verify email using Hunter.io verification API."""
        if not settings.hunter_api_key:
            return {"status": "unknown", "reason": "No Hunter API key"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.hunter.io/v2/email-verifier",
                params={"email": email, "api_key": settings.hunter_api_key},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                "status": data.get("status", "unknown"),
                "score": data.get("score", 0),
                "reason": data.get("result", ""),
            }

    @staticmethod
    def check_mx_record(domain: str) -> bool:
        """Check if domain has valid MX records."""
        try:
            records = dns.resolver.resolve(domain, "MX")
            return len(records) > 0
        except Exception:
            return False

    @staticmethod
    def is_disposable(email: str) -> bool:
        """Check if email is from a disposable provider."""
        domain = email.split("@")[-1].lower()
        return domain in EmailVerifier.DISPOSABLE_DOMAINS

    @staticmethod
    def is_valid_format(email: str) -> bool:
        """Basic email format validation."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @classmethod
    async def verify(cls, email: str) -> Dict:
        """Full email verification pipeline."""
        if not cls.is_valid_format(email):
            return {"status": "invalid", "reason": "Invalid format"}

        if cls.is_disposable(email):
            return {"status": "invalid", "reason": "Disposable email"}

        domain = email.split("@")[-1]
        if not cls.check_mx_record(domain):
            return {"status": "invalid", "reason": "No MX record"}

        # Use Hunter for deep verification if available
        if settings.hunter_api_key:
            return await cls.verify_with_hunter(email)

        return {"status": "valid", "reason": "MX record found", "score": 70}


def get_lead_client(source: str):
    """Factory for lead API clients."""
    if source == "apollo":
        if not settings.apollo_api_key:
            raise ValueError("APOLLO_API_KEY not configured")
        return ApolloClient(settings.apollo_api_key)
    elif source == "hunter":
        if not settings.hunter_api_key:
            raise ValueError("HUNTER_API_KEY not configured")
        return HunterClient(settings.hunter_api_key)
    else:
        raise ValueError(f"Unknown lead source: {source}")
