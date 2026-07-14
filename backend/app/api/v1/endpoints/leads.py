"""Lead management endpoints."""

import csv
import io
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.lead import Lead, LeadList
from app.schemas.lead import (
    LeadCreate, LeadResponse, LeadSearchRequest,
    LeadListResponse, LeadListDetail, AIEnrichRequest, CSVUploadResponse,
)
from app.services.lead_service import get_lead_client, EmailVerifier
from app.tasks.campaign_tasks import enrich_leads_with_ai, verify_leads

router = APIRouter(prefix="/leads", tags=["leads"])


# ── Lead Lists ────────────────────────────────────────────

@router.get("/lists", response_model=List[LeadListResponse])
async def get_lead_lists(
    skip: int = 0, limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LeadList)
        .where(LeadList.user_id == user.id)
        .order_by(LeadList.created_at.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/lists/{list_id}", response_model=LeadListDetail)
async def get_lead_list(
    list_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LeadList)
        .options(selectinload(LeadList.leads))
        .where(LeadList.id == list_id, LeadList.user_id == user.id)
    )
    lead_list = result.scalar_one_or_none()
    if not lead_list:
        raise HTTPException(status_code=404, detail="Lead list not found")
    return lead_list


@router.delete("/lists/{list_id}")
async def delete_lead_list(
    list_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LeadList).where(LeadList.id == list_id, LeadList.user_id == user.id)
    )
    lead_list = result.scalar_one_or_none()
    if not lead_list:
        raise HTTPException(status_code=404, detail="Lead list not found")
    await db.delete(lead_list)
    return {"detail": "Deleted"}


# ── Lead Search (API-based) ──────────────────────────────

@router.post("/search", response_model=LeadListResponse)
async def search_leads(
    data: LeadSearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search for leads using Apollo/Hunter API."""
    if user.credits_remaining < data.limit:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    client = get_lead_client(data.source)
    leads_data = await client.search_people(data.query, per_page=min(data.limit, 25))

    # Create lead list
    lead_list = LeadList(
        user_id=user.id,
        name=f"Search: {data.query[:100]}",
        query=data.query,
        source=data.source,
        total_leads=len(leads_data),
    )
    db.add(lead_list)
    await db.flush()

    # Create leads
    for lead_data in leads_data[:data.limit]:
        if not lead_data.get("email"):
            continue
        lead = Lead(lead_list_id=lead_list.id, **lead_data)
        db.add(lead)

    user.credits_remaining -= min(len(leads_data), data.limit)
    await db.commit()
    return lead_list


# ── CSV Upload ────────────────────────────────────────────

@router.post("/upload-csv", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    list_name: str = Query(default="CSV Import"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload leads from CSV file. Required column: email."""
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    if "email" not in reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV must have 'email' column")

    lead_list = LeadList(
        user_id=user.id,
        name=list_name,
        query=f"CSV upload: {file.filename}",
        source="manual",
        total_leads=0,
    )
    db.add(lead_list)
    await db.flush()

    imported = 0
    skipped = 0
    for row in reader:
        row = {k: (v or "").strip() for k, v in row.items()}
        if not row.get("email"):
            skipped += 1
            continue

        lead = Lead(
            lead_list_id=lead_list.id,
            email=row["email"],
            first_name=row.get("first_name", row.get("name", "").split()[0] if row.get("name") else ""),
            last_name=row.get("last_name", " ".join(row.get("name", "").split()[1:]) if row.get("name") else ""),
            job_title=row.get("job_title", row.get("title", "")),
            company=row.get("company", row.get("organization", "")),
            company_website=row.get("website", row.get("company_website", "")),
            linkedin_url=row.get("linkedin", row.get("linkedin_url", "")),
            phone=row.get("phone", ""),
            location=row.get("location", row.get("city", "")),
            industry=row.get("industry", ""),
        )
        db.add(lead)
        imported += 1

    lead_list.total_leads = imported
    await db.commit()
    return CSVUploadResponse(total_imported=imported, total_skipped=skipped, list_id=lead_list.id)


# ── AI Enrichment ─────────────────────────────────────────

@router.post("/enrich")
async def enrich_leads(
    data: AIEnrichRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI personalized intros for leads."""
    if user.credits_remaining < len(data.lead_ids):
        raise HTTPException(status_code=402, detail="Insufficient credits")

    # Dispatch background task
    task = enrich_leads_with_ai.delay(data.lead_ids, data.tone)
    user.credits_remaining -= len(data.lead_ids)
    await db.commit()
    return {"task_id": task.id, "leads_queued": len(data.lead_ids)}


# ── Email Verification ────────────────────────────────────

@router.post("/verify")
async def verify_lead_emails(
    lead_ids: List[int],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify email addresses for leads."""
    task = verify_leads.delay(lead_ids)
    return {"task_id": task.id, "leads_queued": len(lead_ids)}


# ── Individual Lead ──────────────────────────────────────

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await db.delete(lead)
    return {"detail": "Deleted"}
