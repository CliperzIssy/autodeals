import json
import logging
from pathlib import Path

from app.ai.client import get_model

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "translate.txt"


def _get_model():
    return get_model()


async def translate_to_dutch(
    listing: dict,
    red_flags: dict | None = None,
    deal_score: dict | None = None,
) -> str:
    """Generate a concise Dutch summary of a car listing for Dutch dealers.

    Args:
        listing: Dict with listing details.
        red_flags: Red flag analysis result dict.
        deal_score: Deal score analysis result dict.

    Returns:
        Dutch summary string (max ~150 words).
    """
    if not listing:
        logger.warning("translate_to_dutch called with empty listing")
        return ""

    try:
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

        # Build a readable listing summary
        listing_summary = _format_listing_for_translation(listing)

        prompt = prompt_template.format(
            listing=json.dumps(listing_summary, ensure_ascii=False, indent=2),
            red_flags=json.dumps(red_flags or {}, ensure_ascii=False, indent=2),
            deal_score=json.dumps(deal_score or {}, ensure_ascii=False, indent=2),
        )

        model = _get_model()
        response = model.generate_content(prompt)

        summary = response.text.strip()
        logger.info("Dutch translation complete: %d characters", len(summary))
        return summary

    except Exception as e:
        logger.error("Gemini Dutch translation failed: %s", e)
        return ""


def _format_listing_for_translation(listing: dict) -> dict:
    """Format listing data for the translation prompt."""
    price_cents = listing.get("price_cents")
    return {
        "titel": listing.get("title", ""),
        "merk": listing.get("make"),
        "model": listing.get("model"),
        "variant": listing.get("variant"),
        "bouwjaar": listing.get("year"),
        "km_stand": listing.get("km"),
        "prijs_eur": price_cents / 100 if price_cents else None,
        "brandstof": listing.get("fuel_type"),
        "transmissie": listing.get("transmission"),
        "vermogen_pk": listing.get("power_hp"),
        "kleur": listing.get("color"),
        "verkoper_type": listing.get("seller_type"),
        "verkoper_land": listing.get("seller_country"),
        "beschrijving": (listing.get("description") or "")[:500],
    }
