"""Deduplication utilities for scraped listings."""

import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Listing

logger = logging.getLogger(__name__)


def generate_content_hash(
    source: str,
    source_id: str,
    price_cents: int | None,
    km: int | None,
) -> str:
    """Create a SHA-256 hash that captures the mutable fields of a listing.

    The hash is built from the composite of *source*, *source_id*, *price_cents*
    and *km*.  When a listing's price or mileage changes on the source site the
    hash will differ, signalling that an update is needed.
    """
    payload = f"{source}:{source_id}:{price_cents}:{km}"
    return hashlib.sha256(payload.encode()).hexdigest()


async def dedup_listings(
    db_session: AsyncSession,
    raw_listings: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Split *raw_listings* into new and updated listings.

    Each dict in *raw_listings* must contain at least the keys ``source``,
    ``source_id``, ``price_cents`` and ``km``.

    Returns
    -------
    (new_listings, updated_listings, unchanged_listings)
        *new_listings* – dicts that have no existing row in the database.
        *updated_listings* – dicts whose ``(source, source_id)`` already exist
        but whose content hash differs (i.e. price or km changed).  Each dict
        in this list is enriched with ``"existing_listing_id"`` so callers can
        perform an UPDATE.
        *unchanged_listings* – dicts whose rows already exist with unchanged
        content hash. They still include ``"existing_listing_id"`` so callers
        can link them to searches.
    """
    if not raw_listings:
        return [], [], []

    # Deduplicate within this scrape batch first. Some sources repeat the same
    # listing across pages (e.g. promoted cards), which can otherwise trigger a
    # unique-constraint failure on insert.
    unique_raw: dict[tuple[str, str], dict] = {}
    for raw in raw_listings:
        key = (raw["source"], raw["source_id"])
        existing = unique_raw.get(key)
        if existing is None:
            unique_raw[key] = raw
            continue

        # Keep the richer payload if duplicate cards have different field sets.
        existing_score = sum(1 for v in existing.values() if v not in (None, "", []))
        new_score = sum(1 for v in raw.values() if v not in (None, "", []))
        if new_score > existing_score:
            unique_raw[key] = raw

    deduped_raw_listings = list(unique_raw.values())
    pairs = list(unique_raw.keys())

    # Fetch existing listings that match any of the (source, source_id) pairs.
    stmt = select(Listing).where(tuple_(Listing.source, Listing.source_id).in_(pairs))
    result = await db_session.execute(stmt)
    existing_listings = result.scalars().all()

    # Build lookup: (source, source_id) -> Listing
    existing_map: dict[tuple[str, str], Listing] = {
        (l.source, l.source_id): l for l in existing_listings
    }

    new_listings: list[dict] = []
    updated_listings: list[dict] = []
    unchanged_listings: list[dict] = []

    for raw in deduped_raw_listings:
        source = raw["source"]
        source_id = raw["source_id"]
        content_hash = generate_content_hash(
            source, source_id, raw.get("price_cents"), raw.get("km"),
        )
        raw["content_hash"] = content_hash

        existing = existing_map.get((source, source_id))
        if existing is None:
            raw["first_seen_at"] = datetime.now(timezone.utc)
            raw["last_seen_at"] = datetime.now(timezone.utc)
            new_listings.append(raw)
            logger.debug("New listing: %s/%s", source, source_id)
        else:
            # Always bump last_seen_at
            raw["existing_listing_id"] = existing.id
            raw["last_seen_at"] = datetime.now(timezone.utc)

            if existing.content_hash != content_hash:
                updated_listings.append(raw)
                logger.info(
                    "Listing changed: %s/%s (hash %s -> %s)",
                    source,
                    source_id,
                    existing.content_hash,
                    content_hash,
                )
            else:
                # No material change – just touch last_seen_at on the ORM object.
                existing.last_seen_at = datetime.now(timezone.utc)
                unchanged_listings.append(raw)
                logger.debug("Listing unchanged: %s/%s", source, source_id)

    logger.info(
        "Dedup result: %d new, %d updated, %d unchanged out of %d raw",
        len(new_listings),
        len(updated_listings),
        len(deduped_raw_listings) - len(new_listings) - len(updated_listings),
        len(deduped_raw_listings),
    )
    return new_listings, updated_listings, unchanged_listings
