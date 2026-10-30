"""Celery task that checks for searches due for scanning and enqueues scrape tasks."""

import logging
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_

from app.tasks.celery_app import celery_app
from app.tasks.async_runner import run_async
from app.database import async_session
from app.models.search import Search

logger = logging.getLogger(__name__)


async def _check_due_searches() -> int:
    """Find searches that are due for scanning and enqueue scrape tasks.

    A search is due when:
    - It is active, AND
    - It has never been scanned (last_scanned_at is NULL), OR
    - last_scanned_at + scan_interval_minutes < now

    Returns:
        The number of scrape tasks enqueued.
    """
    from app.tasks.scrape_task import scrape_search_task

    now = datetime.now(timezone.utc)
    queued_count = 0

    async with async_session() as db:
        # Fetch all active searches
        result = await db.execute(
            select(Search).where(Search.is_active.is_(True))
        )
        searches = result.scalars().all()

        due_searches = []
        for search in searches:
            if search.last_scanned_at is None:
                # Never scanned -- due immediately
                due_searches.append(search)
            else:
                due_at = search.last_scanned_at + timedelta(minutes=search.scan_interval_minutes)
                if due_at <= now:
                    due_searches.append(search)

        if not due_searches:
            logger.debug("No searches are due for scanning")
            return 0

        logger.info("Found %d searches due for scanning", len(due_searches))

        for search in due_searches:
            sources = search.sources or ["mobile_de", "autoscout24"]
            for source in sources:
                # Add random stagger (0-30s) between tasks to avoid burst
                stagger = random.uniform(0, 30)
                scrape_search_task.apply_async(
                    args=[str(search.id), source],
                    countdown=stagger,
                )
                queued_count += 1
                logger.info(
                    "Queued scrape for search %s (%s) / %s with %.1fs stagger",
                    search.id, search.name, source, stagger,
                )

    logger.info("Scheduler queued %d scrape tasks total", queued_count)
    return queued_count


@celery_app.task(name="app.tasks.scheduler.check_due_searches")
def check_due_searches() -> int:
    """Celery task: check for due searches and enqueue scrape tasks.

    Returns:
        Number of scrape tasks enqueued.
    """
    try:
        count = run_async(_check_due_searches())
        return count
    except Exception:
        logger.exception("check_due_searches task failed")
        raise
