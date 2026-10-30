"""Celery task for scraping a search from a specific source."""

import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.tasks.celery_app import celery_app
from app.tasks.async_runner import run_async
from app.database import async_session
from app.models.search import Search
from app.models.scan_log import ScanLog
from app.services import listing_service

logger = logging.getLogger(__name__)


def _get_scraper(source: str):
    """Instantiate the appropriate scraper for the given source."""
    if source == "mobile_de":
        from app.scrapers.mobile_de import MobileDeScraper
        return MobileDeScraper()
    elif source == "autoscout24":
        from app.scrapers.autoscout24 import AutoScout24Scraper
        return AutoScout24Scraper()
    else:
        raise ValueError(f"Unknown scraper source: {source}")


async def _run_scrape(search_id: str, source: str) -> None:
    """Async implementation of the scrape task."""
    search_uuid = uuid.UUID(search_id)
    scraper = _get_scraper(source)
    started_at = datetime.now(timezone.utc)
    start_time = time.monotonic()

    async with async_session() as db:
        scan_log: ScanLog | None = None
        try:
            # Load the search from DB
            result = await db.execute(
                select(Search).where(Search.id == search_uuid)
            )
            search = result.scalar_one_or_none()
            if search is None:
                logger.error("Search %s not found in database", search_id)
                return

            # Reuse queued/running scan log created by trigger endpoint when available.
            existing_log_stmt = (
                select(ScanLog)
                .where(
                    ScanLog.search_id == search_uuid,
                    ScanLog.source == source,
                    ScanLog.status.in_(("queued", "running")),
                    ScanLog.completed_at.is_(None),
                )
                .order_by(ScanLog.started_at.desc())
                .limit(1)
            )
            scan_log = (await db.execute(existing_log_stmt)).scalar_one_or_none()
            if scan_log is None:
                scan_log = ScanLog(
                    search_id=search_uuid,
                    source=source,
                    status="running",
                    started_at=started_at,
                )
                db.add(scan_log)
                await db.flush()
            else:
                scan_log.status = "running"

            # Run the scraper
            logger.info(
                "Starting scrape for search %s (%s) from %s",
                search_id, search.name, source,
            )
            raw_listings = await scraper.scrape_search(search)

            # Save results
            save_result = await listing_service.save_listings(
                db=db,
                search_id=search_uuid,
                raw_listings=raw_listings,
                source=source,
            )

            duration = time.monotonic() - start_time

            # Finalize scan log entry
            if scan_log is None:
                scan_log = ScanLog(search_id=search_uuid, source=source, status="running", started_at=started_at)
                db.add(scan_log)
            scan_log.status = "success"
            scan_log.listings_found = len(raw_listings)
            scan_log.new_listings = save_result["new"]
            scan_log.updated_listings = save_result["updated"]
            scan_log.duration_seconds = round(duration, 2)
            scan_log.completed_at = datetime.now(timezone.utc)

            # Update last_scanned_at on the search
            search.last_scanned_at = datetime.now(timezone.utc)

            await db.commit()

            logger.info(
                "Scrape complete for search %s / %s: %d found, %d new, %d updated (%.1fs)",
                search_id, source,
                len(raw_listings),
                save_result["new"],
                save_result["updated"],
                duration,
            )

            # Queue AI processing for unprocessed listings
            if save_result["new"] > 0:
                from app.tasks.ai_process_task import process_listing_task
                from app.models.listing import Listing, SearchListing
                result2 = await db.execute(
                    select(Listing.id)
                    .join(SearchListing, SearchListing.listing_id == Listing.id)
                    .where(
                        SearchListing.search_id == search_uuid,
                        Listing.source == source,
                        Listing.ai_processed_at.is_(None),
                    )
                )
                unprocessed_ids = [str(row[0]) for row in result2.all()]
                for lid in unprocessed_ids:
                    process_listing_task.delay(lid)
                logger.info("Queued AI processing for %d listings", len(unprocessed_ids))

        except Exception as exc:
            duration = time.monotonic() - start_time
            logger.exception(
                "Scrape failed for search %s / %s after %.1fs",
                search_id, source, duration,
            )

            # Mark failure on existing running log when possible.
            try:
                if scan_log is not None:
                    scan_log.status = "failed"
                    scan_log.error_message = str(exc)[:1000]
                    scan_log.duration_seconds = round(duration, 2)
                    scan_log.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    return
            except Exception:
                logger.exception("Failed to update running scan log for search %s", search_id)

            # Fallback: use a fresh DB session to save failure log.
            try:
                async with async_session() as error_db:
                    scan_log = ScanLog(
                        search_id=search_uuid,
                        source=source,
                        status="failed",
                        error_message=str(exc)[:1000],
                        duration_seconds=round(duration, 2),
                        started_at=started_at,
                        completed_at=datetime.now(timezone.utc),
                    )
                    error_db.add(scan_log)
                    await error_db.commit()
            except Exception:
                logger.exception("Failed to save error scan log for search %s", search_id)


def _queue_ai_processing(db, search_uuid: uuid.UUID, source: str) -> None:
    """Enqueue AI processing tasks for newly scraped listings."""
    from app.tasks.ai_process_task import process_listing_task

    async def _get_unprocessed_ids():
        from app.models.listing import Listing, SearchListing
        result = await db.execute(
            select(Listing.id)
            .join(SearchListing, SearchListing.listing_id == Listing.id)
            .where(
                SearchListing.search_id == search_uuid,
                Listing.source == source,
                Listing.ai_processed_at.is_(None),
            )
        )
        return [str(row[0]) for row in result.all()]

    try:
        listing_ids = run_async(_get_unprocessed_ids())
        for listing_id in listing_ids:
            process_listing_task.delay(listing_id)
        logger.info(
            "Queued AI processing for %d listings from search %s / %s",
            len(listing_ids), search_uuid, source,
        )
    except Exception:
        logger.exception(
            "Failed to queue AI processing for search %s / %s",
            search_uuid, source,
        )


@celery_app.task(name="app.tasks.scrape_task.scrape_search_task", bind=True, max_retries=2)
def scrape_search_task(self, search_id: str, source: str) -> None:
    """Celery task: scrape listings for a search from a specific source.

    Args:
        search_id: UUID string of the Search to scrape.
        source: Source identifier ("mobile_de" or "autoscout24").
    """
    try:
        run_async(_run_scrape(search_id, source))
    except Exception as exc:
        logger.exception(
            "scrape_search_task failed for search %s / %s", search_id, source,
        )
        raise self.retry(exc=exc, countdown=60)
