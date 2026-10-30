import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models import User
from app.services import listing_service
from app.services.contact_service import scrape_contact

router = APIRouter(prefix="/api/listings", tags=["listings"])


def _normalize_sort(sort: Optional[str], sort_by: Optional[str]) -> str:
    candidate = (sort_by or sort or "price_asc").strip().lower()
    alias_map = {
        "score": "score_desc",
        "km": "km_asc",
    }
    return alias_map.get(candidate, candidate)


def _km_range_to_bucket(km_min: Optional[int], km_max: Optional[int]) -> Optional[str]:
    if km_min is None and km_max is None:
        return None
    if km_min == 0 and km_max == 50_000:
        return "0-50k"
    if km_min == 50_000 and km_max == 100_000:
        return "50-100k"
    if km_min == 100_000 and km_max == 150_000:
        return "100-150k"
    if km_min == 150_000 and km_max is None:
        return "150k+"
    return None


# ---------- Schemas ----------

class ListingResponse(BaseModel):
    id: uuid.UUID
    source: str
    source_id: str
    source_url: str
    make: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    km: Optional[int] = None
    price_cents: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    power_hp: Optional[int] = None
    seller_type: Optional[str] = None
    seller_city: Optional[str] = None
    seller_country: Optional[str] = None
    thumbnail_url: Optional[str] = None
    ai_deal_score: Optional[int] = None
    ai_market_avg_price_cents: Optional[int] = None
    ai_price_diff_cents: Optional[int] = None
    ai_red_flags: Optional[Any] = None
    ai_dutch_summary: Optional[str] = None
    estimated_bpm_cents: Optional[int] = None
    estimated_total_cost_cents: Optional[int] = None
    first_seen_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class ListingDetailResponse(ListingResponse):
    description: Optional[str] = None
    normalized_title: Optional[str] = None
    image_urls: Optional[list] = None
    seller_name: Optional[str] = None
    seller_phone: Optional[str] = None
    seller_zip: Optional[str] = None
    power_kw: Optional[int] = None
    engine_size_cc: Optional[int] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    doors: Optional[int] = None
    month_registered: Optional[int] = None
    ai_processed_at: Optional[datetime] = None
    last_seen_at: datetime
    created_at: datetime


class PaginatedListingsResponse(BaseModel):
    items: List[ListingResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ContactResponse(BaseModel):
    listing_id: uuid.UUID
    phone_number: Optional[str] = None
    message: str


# ---------- Routes ----------

@router.get("/search/{search_id}", response_model=PaginatedListingsResponse)
async def get_listings_for_search(
    search_id: uuid.UUID,
    sort: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    km_bucket: Optional[str] = Query(None),
    km_min: Optional[int] = Query(None, ge=0),
    km_max: Optional[int] = Query(None, ge=0),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    effective_sort = _normalize_sort(sort, sort_by)
    effective_bucket = km_bucket or _km_range_to_bucket(km_min, km_max)

    result = await listing_service.get_search_listings(
        db,
        search_id=search_id,
        sort_by=effective_sort,
        km_bucket=effective_bucket,
        min_score=min_score,
        page=page,
        per_page=per_page,
    )
    return result


@router.get("/{listing_id}", response_model=ListingDetailResponse)
async def get_listing_detail(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await listing_service.get_listing_detail(db, listing_id)
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


@router.post("/{listing_id}/contact", response_model=ContactResponse)
async def get_contact(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await listing_service.get_listing_detail(db, listing_id)
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    phone = await scrape_contact(listing_id, db)
    return {
        "listing_id": listing_id,
        "phone_number": phone,
        "message": "Contact info retrieved" if phone else "No contact info available",
    }


@router.post("/{listing_id}/scrape-contact", response_model=ContactResponse)
async def scrape_contact_legacy(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy alias used by older frontend builds."""
    return await get_contact(listing_id=listing_id, current_user=current_user, db=db)
