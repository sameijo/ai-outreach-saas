"""Lead schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class LeadCreate(BaseModel):
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    job_title: str = ""
    company: str = ""
    company_website: str = ""
    linkedin_url: str = ""
    phone: str = ""
    location: str = ""
    industry: str = ""


class LeadResponse(BaseModel):
    id: int
    email: str
    email_verified: bool
    verification_status: str
    first_name: str
    last_name: str
    job_title: str
    company: str
    company_website: str
    linkedin_url: str
    phone: str
    location: str
    industry: str
    ai_intro: str
    ai_enriched: bool
    is_contacted: bool
    is_replied: bool
    is_bounced: bool
    is_unsubscribed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LeadSearchRequest(BaseModel):
    query: str  # e.g. "Real Estate Agents in New York"
    source: str = "apollo"  # apollo, hunter
    limit: int = 50


class LeadListResponse(BaseModel):
    id: int
    name: str
    query: str
    source: str
    total_leads: int
    created_at: datetime

    class Config:
        from_attributes = True


class LeadListDetail(LeadListResponse):
    leads: List[LeadResponse] = []


class AIEnrichRequest(BaseModel):
    lead_ids: List[int]
    tone: str = "professional"  # professional, casual, persuasive


class CSVUploadResponse(BaseModel):
    total_imported: int
    total_skipped: int
    list_id: int
