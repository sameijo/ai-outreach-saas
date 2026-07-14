"""Lead and LeadList models."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class LeadList(Base):
    __tablename__ = "lead_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)  # original search query
    source = Column(String(50), default="apollo")  # apollo, hunter, manual
    total_leads = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="lead_lists")
    leads = relationship("Lead", back_populates="lead_list", cascade="all, delete-orphan")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_list_id = Column(Integer, ForeignKey("lead_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    verification_status = Column(String(50), default="unknown")  # valid, invalid, unknown, catch_all
    first_name = Column(String(255), default="")
    last_name = Column(String(255), default="")
    job_title = Column(String(255), default="")
    company = Column(String(255), default="")
    company_website = Column(String(500), default="")
    linkedin_url = Column(String(500), default="")
    phone = Column(String(50), default="")
    location = Column(String(255), default="")
    industry = Column(String(255), default="")
    company_size = Column(String(50), default="")
    # AI enrichment
    ai_intro = Column(Text, default="")
    ai_enriched = Column(Boolean, default=False)
    enrichment_data = Column(Text, default="{}")  # JSON blob
    # Metadata
    is_contacted = Column(Boolean, default=False)
    is_replied = Column(Boolean, default=False)
    is_bounced = Column(Boolean, default=False)
    is_unsubscribed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    lead_list = relationship("LeadList", back_populates="leads")
    email_events = relationship("EmailEvent", back_populates="lead", cascade="all, delete-orphan")
