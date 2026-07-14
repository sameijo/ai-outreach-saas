"""Campaign and EmailEvent models."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="draft")  # draft, active, paused, completed
    lead_list_id = Column(Integer, ForeignKey("lead_lists.id", ondelete="SET NULL"), nullable=True)
    smtp_config_id = Column(Integer, ForeignKey("smtp_configs.id", ondelete="SET NULL"), nullable=True)
    # Email content
    subject = Column(String(500), nullable=False, default="")
    body_html = Column(Text, nullable=False, default="")
    body_text = Column(Text, default="")
    # Follow-up sequence
    follow_ups = Column(JSON, default=[])  # [{delay_hours, subject, body_html, body_text}]
    # Settings
    send_rate_per_hour = Column(Integer, default=30)
    send_rate_per_day = Column(Integer, default=200)
    send_window_start = Column(String(10), default="09:00")  # HH:MM
    send_window_end = Column(String(10), default="17:00")
    timezone = Column(String(50), default="UTC")
    personalize_with_ai = Column(Boolean, default=True)
    ai_tone = Column(String(50), default="professional")  # professional, casual, persuasive
    ab_test_config = Column(Text, nullable=True)  # JSON config for A/B tests
    # Stats (denormalized for fast dashboard)
    total_leads = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    emails_failed = Column(Integer, default=0)
    # Timestamps
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="campaigns")
    email_events = relationship("EmailEvent", back_populates="campaign", cascade="all, delete-orphan")


class EmailEvent(Base):
    __tablename__ = "email_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    # Message details
    message_id = Column(String(255), default="")  # provider message ID
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), default="")
    body_html = Column(Text, default="")
    # Status
    status = Column(String(50), default="queued")  # queued, sending, sent, delivered, opened, clicked, replied, bounced, failed, unsubscribed
    follow_up_step = Column(Integer, default=0)  # 0 = initial, 1+ = follow-ups
    # Tracking
    tracking_id = Column(String(100), unique=True, nullable=False, index=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    open_count = Column(Integer, default=0)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    click_count = Column(Integer, default=0)
    clicked_urls = Column(JSON, default=[])
    replied_at = Column(DateTime(timezone=True), nullable=True)
    bounced_at = Column(DateTime(timezone=True), nullable=True)
    bounce_reason = Column(Text, default="")
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # Warm-up
    is_warmup = Column(Boolean, default=False)
    smtp_config_id = Column(Integer, nullable=True)

    campaign = relationship("Campaign", back_populates="email_events")
    lead = relationship("Lead", back_populates="email_events")


class SMTPConfig(Base):
    __tablename__ = "smtp_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)  # sendgrid, ses, mailgun, resend, smtp
    # SMTP specific
    smtp_host = Column(String(255), default="")
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String(255), default="")
    smtp_password = Column(String(500), default="")
    smtp_use_tls = Column(Boolean, default=True)
    # Provider API key
    api_key = Column(String(500), default="")
    # Sender info
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), default="")
    reply_to = Column(String(255), default="")
    # Warm-up
    daily_limit = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="smtp_configs")
