"""Service layer for Listing persistence and retrieval."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Listing, SearchListing
from app.utils.dedup import dedup_listings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

async def save_listings(
    db: AsyncSession,
    search_id: uuid.UUID,
    raw_listings: list[dict],
    source: str,
) -> dict[str, int]:
    """Persist scraped listings, handling dedup and search-linking.

    Each dict in *raw_listings* should contain keys matching :class:`Listing`
    columns (at minimum ``source``, ``source_id``, ``price_cents``, ``km``).

    Returns a summary dict: ``{"new": n, "updated": n}``.
    """
    if not raw_listings:
        return {"new": 0, "updated": 0}

    # Ensure every listing has the source tag
    for r in raw_listings:
        r.setdefault("source", source)

    new, updated, unchanged = await dedup_listings(db, raw_listings)

    # --- Insert brand-new listings ---
    new_listing_ids: list[uuid.UUID] = []
    new_listing_objects: list[Listing] = []
    for raw in new:
        raw.pop("existing_listing_id", None)
        listing = Listing(**{
            k: v for k, v in raw.items()
            if hasattr(Listing, k)
        })
        db.add(listing)
        new_listing_objects.append(listing)

    if new_listing_objects:
        await db.flush()
        new_listing_ids = [listing.id for listing in new_listing_objects]

    # --- Update changed listings ---
    updated_listing_ids: list[uuid.UUID] = []
    for raw in updated:
        listing_id = raw.pop("existing_listing_id")
        updated_listing_ids.append(listing_id)

        values: dict = {}
        for key in ("price_cents", "km", "content_hash", "last_seen_at"):
            if key in raw:
                values[key] = raw[key]
        values["updated_at"] = datetime.now(timezone.utc)

        await db.execute(
            update(Listing).where(Listing.id == listing_id).values(**values)
        )

    # --- Link all (new + updated + unchanged) listings to this search ---
    unchanged_listing_ids: list[uuid.UUID] = []
    for raw in unchanged:
        listing_id = raw.get("existing_listing_id")
        if listing_id:
            unchanged_listing_ids.append(listing_id)

    all_ids = new_listing_ids + updated_listing_ids + unchanged_listing_ids
    for lid in all_ids:
        # Avoid duplicate links
        exists = await db.execute(
            select(SearchListing).where(
                SearchListing.search_id == search_id,
                SearchListing.listing_id == lid,
            )
        )
        if exists.scalar_one_or_none() is None:
            db.add(SearchListing(search_id=search_id, listing_id=lid))

    await db.flush()
    logger.info(
        "save_listings for search %s: %d new, %d updated, %d linked_unchanged",
        search_id, len(new), len(updated), len(unchanged_listing_ids),
    )
    return {"new": len(new), "updated": len(updated)}


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

async def get_search_listings(
    db: AsyncSession,
    search_id: uuid.UUID,
    *,
    sort_by: str = "price_asc",
    km_bucket: str | None = None,
    min_score: int | None = None,
    page: int = 1,
    per_page: int = 25,
) -> dict:
    """Return paginated, filtered listings linked to a search.

    Parameters
    ----------
    sort_by:
        One of ``price_asc``, ``price_desc``, ``score_desc``, ``km_asc``,
        ``newest``.
    km_bucket:
        Optional mileage bucket string, e.g. ``"50-100k"``.  Translated to a
        WHERE clause on ``Listing.km``.
    min_score:
        If provided, only listings with ``ai_deal_score >= min_score`` are
        returned.
    page / per_page:
        Standard pagination.

    Returns
    -------
    dict with keys ``items``, ``total``, ``page``, ``per_page``, ``pages``.
    """
    base = (
        select(Listing)
        .join(SearchListing, SearchListing.listing_id == Listing.id)
        .where(
            SearchListing.search_id == search_id,
            Listing.is_active.is_(True),
        )
    )

    # --- KM bucket filter ---
    km_ranges: dict[str, tuple[int | None, int | None]] = {
        "0-50k": (0, 50_000),
        "50-100k": (50_000, 100_000),
        "100-150k": (100_000, 150_000),
        "150k+": (150_000, None),
    }
    if km_bucket and km_bucket in km_ranges:
        low, high = km_ranges[km_bucket]
        if low is not None:
            base = base.where(Listing.km >= low)
        if high is not None:
            base = base.where(Listing.km < high)

    # --- Score filter ---
    if min_score is not None:
        base = base.where(Listing.ai_deal_score >= min_score)

    # --- Sorting ---
    order_map = {
        "price_asc": Listing.price_cents.asc(),
        "price_desc": Listing.price_cents.desc(),
        "score_desc": Listing.ai_deal_score.desc().nulls_last(),
        "km_asc": Listing.km.asc(),
        "newest": Listing.first_seen_at.desc(),
    }
    order = order_map.get(sort_by, Listing.price_cents.asc())
    base = base.order_by(order)

    # --- Count ---
    count_stmt = select(func.count()).select_from(base.subquery())
    total: int = (await db.execute(count_stmt)).scalar_one()

    # --- Paginate ---
    offset = (page - 1) * per_page
    data_stmt = base.offset(offset).limit(per_page)
    result = await db.execute(data_stmt)
    items = list(result.scalars().all())

    pages = max(1, (total + per_page - 1) // per_page)

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


async def get_listing_detail(
    db: AsyncSession,
    listing_id: uuid.UUID,
) -> Listing | None:
    """Fetch a single listing with all columns."""
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

async def mark_inactive_listings(
    db: AsyncSession,
    search_id: uuid.UUID,
    source: str,
    current_source_ids: list[str],
) -> int:
    """Mark listings as inactive when they disappear from the source.

    Any listing linked to *search_id* from the given *source* whose
    ``source_id`` is **not** in *current_source_ids* will have ``is_active``
    set to ``False``.

    Returns the number of listings deactivated.
    """
    if not current_source_ids:
        logger.warning(
            "mark_inactive_listings called with empty current_source_ids for "
            "search %s / source %s — skipping to avoid marking everything inactive",
            search_id,
            source,
        )
        return 0

    # Get IDs of listings linked to this search from this source that are
    # NOT in the current scrape result.
    subq = (
        select(SearchListing.listing_id)
        .join(Listing, Listing.id == SearchListing.listing_id)
        .where(
            SearchListing.search_id == search_id,
            Listing.source == source,
            Listing.is_active.is_(True),
            Listing.source_id.notin_(current_source_ids),
        )
    )

    result = await db.execute(
        update(Listing)
        .where(Listing.id.in_(subq))
        .values(is_active=False, updated_at=datetime.now(timezone.utc))
    )

    count = result.rowcount
    if count:
        logger.info(
            "Marked %d listings inactive for search %s / source %s",
            count,
            search_id,
            source,
        )
    return count
