import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models import User, Search, Listing, SearchListing

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ---------- Schemas ----------

class DealSummary(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    km: Optional[int] = None
    price_cents: Optional[int] = None
    ai_deal_score: Optional[int] = None
    ai_price_diff_cents: Optional[int] = None
    source_url: str
    source: str
    thumbnail_url: Optional[str] = None
    first_seen_at: datetime

    model_config = {"from_attributes": True}


class DashboardStatsResponse(BaseModel):
    active_searches: int
    total_listings: int
    new_today: int
    top_deals: List[DealSummary]


# ---------- Routes ----------

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id

    # Active searches count
    result = await db.execute(
        select(func.count(Search.id)).where(Search.user_id == user_id, Search.is_active.is_(True))
    )
    active_searches = result.scalar_one()

    # Total active listings linked to user's searches
    result = await db.execute(
        select(func.count(Listing.id))
        .join(SearchListing, SearchListing.listing_id == Listing.id)
        .join(Search, Search.id == SearchListing.search_id)
        .where(Search.user_id == user_id, Search.is_active.is_(True), Listing.is_active.is_(True))
    )
    total_listings = result.scalar_one()

    # New today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(Listing.id))
        .join(SearchListing, SearchListing.listing_id == Listing.id)
        .join(Search, Search.id == SearchListing.search_id)
        .where(
            Search.user_id == user_id,
            Search.is_active.is_(True),
            Listing.first_seen_at >= today_start,
        )
    )
    new_today = result.scalar_one()

    # Top deals (score > 80)
    result = await db.execute(
        select(Listing)
        .join(SearchListing, SearchListing.listing_id == Listing.id)
        .join(Search, Search.id == SearchListing.search_id)
        .where(
            Search.user_id == user_id,
            Search.is_active.is_(True),
            Listing.is_active.is_(True),
            Listing.ai_deal_score > 80,
        )
        .order_by(Listing.ai_deal_score.desc())
        .limit(20)
    )
    top_deals = list(result.scalars().all())

    return {
        "active_searches": active_searches,
        "total_listings": total_listings,
        "new_today": new_today,
        "top_deals": top_deals,
    }


@router.get("/recent-deals", response_model=List[DealSummary])
async def get_recent_deals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Listing)
        .join(SearchListing, SearchListing.listing_id == Listing.id)
        .join(Search, Search.id == SearchListing.search_id)
        .where(
            Search.user_id == current_user.id,
            Search.is_active.is_(True),
            Listing.is_active.is_(True),
            Listing.ai_deal_score > 65,
        )
        .order_by(Listing.first_seen_at.desc())
        .limit(20)
    )
    return list(result.scalars().all())
