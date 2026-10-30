"""CRUD operations for Search objects."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Search

logger = logging.getLogger(__name__)


async def create_search(db: AsyncSession, user_id: uuid.UUID, **kwargs) -> Search:
    """Create and persist a new Search.

    Accepted keyword arguments correspond to :class:`Search` columns (e.g.
    ``name``, ``make``, ``model``, ``year_min``, etc.).
    """
    search = Search(user_id=user_id, **kwargs)
    db.add(search)
    await db.flush()
    await db.refresh(search)
    logger.info("Created search %s for user %s", search.id, user_id)
    return search


async def get_search(db: AsyncSession, search_id: uuid.UUID) -> Search | None:
    """Return a single Search by primary key, or ``None``."""
    result = await db.execute(select(Search).where(Search.id == search_id))
    return result.scalar_one_or_none()


async def get_user_searches(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    active_only: bool = True,
) -> list[Search]:
    """Return all searches belonging to a user, optionally filtered to active."""
    stmt = select(Search).where(Search.user_id == user_id)
    if active_only:
        stmt = stmt.where(Search.is_active.is_(True))
    stmt = stmt.order_by(Search.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_search(
    db: AsyncSession,
    search_id: uuid.UUID,
    **kwargs,
) -> Search | None:
    """Update mutable fields on an existing Search.

    Returns the refreshed Search, or ``None`` if not found.
    """
    search = await get_search(db, search_id)
    if search is None:
        logger.warning("Search %s not found for update", search_id)
        return None

    for key, value in kwargs.items():
        if hasattr(search, key):
            setattr(search, key, value)
        else:
            logger.warning("Ignoring unknown Search attribute: %s", key)

    search.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(search)
    logger.info("Updated search %s", search_id)
    return search


async def delete_search(db: AsyncSession, search_id: uuid.UUID) -> bool:
    """Soft-delete a search by marking it inactive.

    Returns ``True`` if the search existed and was deactivated.
    """
    result = await db.execute(
        update(Search)
        .where(Search.id == search_id)
        .values(is_active=False, updated_at=datetime.now(timezone.utc))
    )
    if result.rowcount:
        logger.info("Soft-deleted search %s", search_id)
        return True
    logger.warning("Search %s not found for deletion", search_id)
    return False


async def get_due_searches(db: AsyncSession) -> list[Search]:
    """Return active searches whose scan interval has elapsed.

    A search is "due" when:
    - It has never been scanned (``last_scanned_at IS NULL``), **or**
    - ``now() - last_scanned_at >= scan_interval_minutes``.
    """
    now = datetime.now(timezone.utc)

    stmt = select(Search).where(
        Search.is_active.is_(True),
    )
    result = await db.execute(stmt)
    all_active: list[Search] = list(result.scalars().all())

    due: list[Search] = []
    for search in all_active:
        if search.last_scanned_at is None:
            due.append(search)
        else:
            next_scan = search.last_scanned_at + timedelta(
                minutes=search.scan_interval_minutes,
            )
            if now >= next_scan:
                due.append(search)

    logger.info(
        "Found %d due searches out of %d active", len(due), len(all_active),
    )
    return due
