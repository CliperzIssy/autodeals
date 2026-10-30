"""Celery task for running the AI pipeline on a single listing."""

import logging
import uuid

from app.tasks.async_runner import run_async
from app.tasks.celery_app import celery_app
from app.database import async_session

logger = logging.getLogger(__name__)


async def _run_ai_pipeline(listing_id: str) -> None:
    """Async implementation of the AI processing task."""
    from app.ai.pipeline import process_listing

    listing_uuid = uuid.UUID(listing_id)

    async with async_session() as db:
        try:
            await process_listing(db_session=db, listing_id=listing_uuid)
            logger.info("AI pipeline completed for listing %s", listing_id)
        except Exception:
            logger.exception("AI pipeline failed for listing %s", listing_id)
            raise


@celery_app.task(name="app.tasks.ai_process_task.process_listing_task", bind=True, max_retries=2)
def process_listing_task(self, listing_id: str) -> None:
    """Celery task: run the AI pipeline on a listing.

    Args:
        listing_id: UUID string of the Listing to process.
    """
    try:
        run_async(_run_ai_pipeline(listing_id))
    except Exception as exc:
        logger.exception("process_listing_task failed for listing %s", listing_id)
        raise self.retry(exc=exc, countdown=30)
