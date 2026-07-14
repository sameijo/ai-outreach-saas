"""Campaign schemas."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class FollowUpStep(BaseModel):
    delay_hours: int = 48
    subject: str
    body_html: str
    body_text: str = ""


class CampaignCreate(BaseModel):
    name: str
    lead_list_id: int
    smtp_config_id: Optional[int] = None
    subject: str
    body_html: str
    body_text: str = ""
    follow_ups: List[FollowUpStep] = []
    send_rate_per_hour: int = 30
    send_rate_per_day: int = 200
    send_window_start: str = "09:00"
    send_window_end: str = "17:00"
    timezone: str = "UTC"
    personalize_with_ai: bool = True
    ai_tone: str = "professional"
    scheduled_at: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    follow_ups: Optional[List[FollowUpStep]] = None
    send_rate_per_hour: Optional[int] = None
    send_rate_per_day: Optional[int] = None
    status: Optional[str] = None


class CampaignResponse(BaseModel):
    id: int
    name: str
    status: str
    lead_list_id: Optional[int]
    subject: str
    personalize_with_ai: bool
    ai_tone: str
    total_leads: int
    emails_sent: int
    emails_opened: int
    emails_clicked: int
    emails_replied: int
    emails_bounced: int
    emails_failed: int
    send_rate_per_hour: int
    send_rate_per_day: int
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignStats(BaseModel):
    total_leads: int
    emails_sent: int
    emails_opened: int
    open_rate: float
    emails_clicked: int
    click_rate: float
    emails_replied: int
    reply_rate: float
    emails_bounced: int
    bounce_rate: float
    emails_failed: int


class SMTPConfigCreate(BaseModel):
    name: str
    provider: str  # sendgrid, ses, mailgun, resend, smtp
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    api_key: str = ""
    from_email: str
    from_name: str = ""
    reply_to: str = ""
    daily_limit: int = 100


class SMTPConfigResponse(BaseModel):
    id: int
    name: str
    provider: str
    from_email: str
    from_name: str
    daily_limit: int
    is_active: bool
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EmailEventResponse(BaseModel):
    id: int
    campaign_id: int
    recipient_email: str
    subject: str
    status: str
    follow_up_step: int
    opened_at: Optional[datetime]
    open_count: int
    clicked_at: Optional[datetime]
    click_count: int
    replied_at: Optional[datetime]
    bounced_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
