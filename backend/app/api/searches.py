import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models import User
from app.models.scan_log import ScanLog
from app.services import listing_service, search_service

router = APIRouter(prefix="/api/searches", tags=["searches"])


# ---------- Schemas ----------

class SearchCreateRequest(BaseModel):
    name: str
    make: str
    model: Optional[str] = None
    variant: Optional[str] = None
    generation: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    km_min: Optional[int] = None
    km_max: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    sources: Optional[List[str]] = None
    scan_interval_minutes: Optional[int] = 60


class SearchUpdateRequest(BaseModel):
    name: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    generation: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    km_min: Optional[int] = None
    km_max: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    scan_interval_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class SearchResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    make: str
    model: Optional[str] = None
    variant: Optional[str] = None
    generation: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    km_min: Optional[int] = None
    km_max: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    sources: Optional[list] = None
    scan_interval_minutes: int
    is_active: bool
    last_scanned_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Routes ----------

@router.post("/", response_model=SearchResponse, status_code=status.HTTP_201_CREATED)
async def create(
    body: SearchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump(exclude_unset=True)
    search = await search_service.create_search(db, user_id=current_user.id, **data)
    return search


@router.get("/", response_model=List[SearchResponse])
async def list_searches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await search_service.get_user_searches(db, user_id=current_user.id)


@router.get("/{search_id}", response_model=SearchResponse)
async def get_search_detail(
    search_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    search = await search_service.get_search(db, search_id)
    if not search or search.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")
    return search


@router.put("/{search_id}", response_model=SearchResponse)
async def update(
    search_id: uuid.UUID,
    body: SearchUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await search_service.get_search(db, search_id)
    if not existing or existing.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    data = body.model_dump(exclude_unset=True)
    updated = await search_service.update_search(db, search_id, **data)
    return updated


@router.delete("/{search_id}", status_code=status.HTTP_200_OK)
async def delete(
    search_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await search_service.get_search(db, search_id)
    if not existing or existing.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    await search_service.delete_search(db, search_id)
    return {"message": "Search deactivated"}


@router.post("/{search_id}/scan")
async def trigger_scan(
    search_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await search_service.get_search(db, search_id)
    if not existing or existing.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    running_cutoff = datetime.now(timezone.utc) - timedelta(minutes=90)
    running_stmt = (
        select(ScanLog)
        .where(
            ScanLog.search_id == search_id,
            ScanLog.status.in_(("queued", "running")),
            ScanLog.completed_at.is_(None),
            ScanLog.started_at >= running_cutoff,
        )
        .limit(1)
    )
    running = (await db.execute(running_stmt)).scalar_one_or_none()
    if running is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A scan is already running for this search. Please wait for it to finish.",
        )

    from app.tasks.scrape_task import scrape_search_task
    sources = existing.sources or ["mobile_de", "autoscout24"]
    task_ids = []
    now = datetime.now(timezone.utc)
    for source in sources:
        db.add(
            ScanLog(
                search_id=search_id,
                source=source,
                status="queued",
                started_at=now,
            )
        )
        task = scrape_search_task.delay(str(search_id), source)
        task_ids.append(task.id)
    return {"message": f"Scan enqueued for {len(sources)} sources", "task_ids": task_ids}


@router.get("/{search_id}/listings")
async def get_search_listings_legacy_route(
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
    """Compatibility route for older clients using /api/searches/{id}/listings."""
    existing = await search_service.get_search(db, search_id)
    if not existing or existing.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    effective_sort = (sort_by or sort or "price_asc").strip().lower()
    if effective_sort == "score":
        effective_sort = "score_desc"
    elif effective_sort == "km":
        effective_sort = "km_asc"

    effective_bucket = km_bucket
    if not effective_bucket:
        if km_min == 0 and km_max == 50_000:
            effective_bucket = "0-50k"
        elif km_min == 50_000 and km_max == 100_000:
            effective_bucket = "50-100k"
        elif km_min == 100_000 and km_max == 150_000:
            effective_bucket = "100-150k"
        elif km_min == 150_000 and km_max is None:
            effective_bucket = "150k+"

    return await listing_service.get_search_listings(
        db=db,
        search_id=search_id,
        sort_by=effective_sort,
        km_bucket=effective_bucket,
        min_score=min_score,
        page=page,
        per_page=per_page,
    )
