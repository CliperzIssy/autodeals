import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.ai.normalizer import normalize_title
from app.ai.red_flags import detect_red_flags
from app.ai.deal_scorer import score_deal
from app.ai.translator import translate_to_dutch

logger = logging.getLogger(__name__)


async def process_listing(db_session: AsyncSession, listing_id: UUID) -> None:
    """Run the full AI pipeline on a listing: normalize, red flags, deal score, translate.

    Each step is independent in terms of error handling -- if one step fails,
    the others still proceed and partial results are saved.

    Args:
        db_session: An async SQLAlchemy session.
        listing_id: The UUID of the listing to process.
    """
    # Load the listing from DB
    result = await db_session.execute(
        select(Listing).where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()

    if listing is None:
        logger.error("Listing %s not found in database", listing_id)
        return

    logger.info("Starting AI pipeline for listing %s (%s)", listing_id, listing.title[:60] if listing.title else "no title")

    listing_dict = _listing_to_dict(listing)
    normalized = None
    red_flags_result = None
    deal_score_result = None
    dutch_summary = None

    # Step 1: Normalize title
    try:
        normalized = await normalize_title(
            title=listing.title or "",
            metadata={
                "year": listing.year,
                "km": listing.km,
                "fuel_type": listing.fuel_type,
                "power_hp": listing.power_hp,
                "transmission": listing.transmission,
            },
        )
        logger.info("Step 1/4 (normalize) complete for listing %s", listing_id)
    except Exception as e:
        logger.error("Step 1/4 (normalize) failed for listing %s: %s", listing_id, e)

    # Step 2: Detect red flags
    try:
        red_flags_result = await detect_red_flags(listing.description or "")
        logger.info("Step 2/4 (red_flags) complete for listing %s", listing_id)
    except Exception as e:
        logger.error("Step 2/4 (red_flags) failed for listing %s: %s", listing_id, e)

    # Step 3: Score the deal
    try:
        comparable_listings = await _find_comparables(db_session, listing)
        deal_score_result = await score_deal(listing_dict, comparable_listings)
        logger.info("Step 3/4 (deal_score) complete for listing %s", listing_id)
    except Exception as e:
        logger.error("Step 3/4 (deal_score) failed for listing %s: %s", listing_id, e)

    # Step 4: Translate to Dutch
    try:
        dutch_summary = await translate_to_dutch(
            listing=listing_dict,
            red_flags=red_flags_result,
            deal_score=deal_score_result,
        )
        logger.info("Step 4/4 (translate) complete for listing %s", listing_id)
    except Exception as e:
        logger.error("Step 4/4 (translate) failed for listing %s: %s", listing_id, e)

    # Update listing with AI results
    try:
        if normalized:
            # Build a normalized title string from the structured data
            parts = [
                normalized.get("make"),
                normalized.get("model"),
                normalized.get("generation"),
                normalized.get("variant"),
                normalized.get("sub_variant"),
                normalized.get("engine_code"),
            ]
            listing.normalized_title = " ".join(p for p in parts if p)

            # Update make/model if not already set
            if not listing.make and normalized.get("make"):
                listing.make = normalized["make"]
            if not listing.model and normalized.get("model"):
                listing.model = normalized["model"]
            if not listing.variant and normalized.get("variant"):
                listing.variant = normalized["variant"]
            if not listing.power_hp and normalized.get("power_hp"):
                listing.power_hp = normalized["power_hp"]

        if red_flags_result:
            listing.ai_red_flags = red_flags_result

        if deal_score_result:
            listing.ai_deal_score = deal_score_result.get("deal_score")
            market_avg = deal_score_result.get("market_avg_price")
            if market_avg:
                listing.ai_market_avg_price_cents = int(market_avg * 100)
            price_diff = deal_score_result.get("price_diff_eur")
            if price_diff is not None:
                listing.ai_price_diff_cents = int(price_diff * 100)

        if dutch_summary:
            listing.ai_dutch_summary = dutch_summary

        listing.ai_processed_at = datetime.now(timezone.utc)

        await db_session.commit()
        logger.info("AI pipeline results saved for listing %s", listing_id)

    except Exception as e:
        logger.error("Failed to save AI pipeline results for listing %s: %s", listing_id, e)
        await db_session.rollback()
        raise


async def _find_comparables(db_session: AsyncSession, listing: Listing) -> list[dict]:
    """Find comparable listings in the database for deal scoring."""
    if not listing.make or not listing.model:
        logger.info("Cannot find comparables: listing has no make/model")
        return []

    try:
        query = (
            select(Listing)
            .where(
                Listing.make == listing.make,
                Listing.model == listing.model,
                Listing.is_active == True,  # noqa: E712
                Listing.id != listing.id,
                Listing.price_cents.isnot(None),
            )
        )

        # Filter by year range if available
        if listing.year:
            query = query.where(
                Listing.year >= listing.year - 2,
                Listing.year <= listing.year + 2,
            )

        query = query.limit(20)

        result = await db_session.execute(query)
        comparables = result.scalars().all()

        return [_listing_to_dict(comp) for comp in comparables]

    except Exception as e:
        logger.error("Failed to find comparable listings: %s", e)
        return []


def _listing_to_dict(listing: Listing) -> dict:
    """Convert a Listing ORM model to a plain dict."""
    return {
        "title": listing.title,
        "make": listing.make,
        "model": listing.model,
        "variant": listing.variant,
        "year": listing.year,
        "km": listing.km,
        "price_cents": listing.price_cents,
        "fuel_type": listing.fuel_type,
        "transmission": listing.transmission,
        "power_hp": listing.power_hp,
        "color": listing.color,
        "seller_type": listing.seller_type,
        "seller_country": listing.seller_country,
        "description": listing.description,
    }
