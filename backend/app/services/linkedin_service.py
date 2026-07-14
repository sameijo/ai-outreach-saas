"""LinkedIn scraping service — extracts public profile data."""

import logging
import httpx
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """Scrape publicly available LinkedIn data."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
    async def scrape_profile(self, linkedin_url: str) -> Dict:
        """Scrape a public LinkedIn profile for context."""
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(linkedin_url, headers=self.HEADERS)
                if resp.status_code != 200:
                    return {"error": f"HTTP {resp.status_code}", "snippet": ""}

            soup = BeautifulSoup(resp.text, "lxml")

            # Extract name
            name_tag = soup.find("h1", class_="text-heading-xlarge")
            name = name_tag.get_text(strip=True) if name_tag else ""

            # Extract headline
            headline_tag = soup.find("div", class_="text-body-medium")
            headline = headline_tag.get_text(strip=True) if headline_tag else ""

            # Extract location
            location_tag = soup.find("span", class_="text-body-small")
            location = location_tag.get_text(strip=True) if location_tag else ""

            # Extract about section
            about_section = soup.find("div", class_="display-flex") 
            about = about_section.get_text(strip=True)[:500] if about_section else ""

            # Extract recent activity snippets
            activity_snippets = []
            activity_sections = soup.find_all("div", class_="feed-shared-update-v2")
            for section in activity_sections[:3]:
                text = section.get_text(strip=True)[:200]
                if text:
                    activity_snippets.append(text)

            return {
                "name": name,
                "headline": headline,
                "location": location,
                "about": about,
                "recent_activity": activity_snippets,
                "snippet": f"{headline}. {about[:200]}",
            }

        except Exception as e:
            logger.error(f"LinkedIn scrape failed for {linkedin_url}: {e}")
            return {"error": str(e), "snippet": ""}

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
    async def scrape_company(self, company_url: str) -> Dict:
        """Scrape a public LinkedIn company page."""
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(company_url, headers=self.HEADERS)
                if resp.status_code != 200:
                    return {"error": f"HTTP {resp.status_code}"}

            soup = BeautifulSoup(resp.text, "lxml")

            name_tag = soup.find("h1")
            name = name_tag.get_text(strip=True) if name_tag else ""

            about_tag = soup.find("p", class_="break-words")
            about = about_tag.get_text(strip=True)[:500] if about_tag else ""

            industry_tag = soup.find("dd", class_="mb4")
            industry = industry_tag.get_text(strip=True) if industry_tag else ""

            return {
                "name": name,
                "about": about,
                "industry": industry,
                "snippet": f"{name} — {about[:200]}",
            }

        except Exception as e:
            logger.error(f"LinkedIn company scrape failed for {company_url}: {e}")
            return {"error": str(e)}

    @staticmethod
    def build_search_url(query: str) -> str:
        """Build a LinkedIn people search URL."""
        import urllib.parse
        return f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(query)}"


async def enrich_lead_from_linkedin(linkedin_url: str) -> str:
    """Get a text snippet from LinkedIn to feed into AI personalization."""
    if not linkedin_url:
        return ""
    
    scraper = LinkedInScraper()
    data = await scraper.scrape_profile(linkedin_url)
    
    if data.get("error"):
        return ""
    
    parts = []
    if data.get("headline"):
        parts.append(data["headline"])
    if data.get("about"):
        parts.append(data["about"][:200])
    if data.get("recent_activity"):
        parts.append("Recent: " + data["recent_activity"][0][:100])
    
    return ". ".join(parts)


linkedin_scraper = LinkedInScraper()
