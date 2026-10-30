import json
import logging
from pathlib import Path

from app.ai.client import get_model

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "deal_score.txt"


def _get_model():
    return get_model()


async def score_deal(listing: dict, comparable_listings: list[dict]) -> dict:
    """Score a deal by comparing a listing against comparable market data.

    Args:
        listing: Dict with listing details (title, price_cents, km, year, etc.).
        comparable_listings: List of comparable listing dicts for market context.

    Returns:
        Dict with deal_score, market_avg_price, price_position,
        price_diff_eur, price_diff_pct, confidence, reasoning.
    """
    if not listing:
        logger.warning("score_deal called with empty listing")
        return _empty_result()

    try:
        # Calculate market context from comparables
        market_context = _build_market_context(comparable_listings)

        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

        # Format listing for the prompt (convert price_cents to EUR)
        listing_summary = _format_listing(listing)
        comparables_summary = _format_comparables(comparable_listings)

        prompt = prompt_template.format(
            listing=json.dumps(listing_summary, ensure_ascii=False),
            comparable_count=market_context["count"],
            avg_price=market_context["avg_price"],
            min_price=market_context["min_price"],
            max_price=market_context["max_price"],
            comparables=json.dumps(comparables_summary, ensure_ascii=False),
        )

        model = _get_model()
        response = model.generate_content(prompt)

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3].strip()

        result = json.loads(raw_text)

        # Ensure deal_score is an integer in range
        result["deal_score"] = max(0, min(100, int(result.get("deal_score", 50))))
        result.setdefault("market_avg_price", market_context["avg_price"])
        result.setdefault("confidence", "low" if market_context["count"] < 3 else "medium")

        logger.info(
            "Deal scoring complete: score=%d, position=%s, confidence=%s",
            result["deal_score"],
            result.get("price_position", "unknown"),
            result.get("confidence", "unknown"),
        )
        return result

    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini JSON response for deal scoring: %s", e)
        return _empty_result()
    except Exception as e:
        logger.error("Gemini deal scoring failed: %s", e)
        return _empty_result()


def _build_market_context(comparable_listings: list[dict]) -> dict:
    """Calculate aggregate market statistics from comparable listings."""
    if not comparable_listings:
        return {"count": 0, "avg_price": 0, "min_price": 0, "max_price": 0}

    prices = []
    for comp in comparable_listings:
        price_cents = comp.get("price_cents")
        if price_cents and price_cents > 0:
            prices.append(price_cents / 100)

    if not prices:
        return {"count": 0, "avg_price": 0, "min_price": 0, "max_price": 0}

    return {
        "count": len(prices),
        "avg_price": int(sum(prices) / len(prices)),
        "min_price": int(min(prices)),
        "max_price": int(max(prices)),
    }


def _format_listing(listing: dict) -> dict:
    """Format a listing dict for the prompt, converting cents to EUR."""
    price_cents = listing.get("price_cents")
    return {
        "title": listing.get("title", ""),
        "make": listing.get("make"),
        "model": listing.get("model"),
        "year": listing.get("year"),
        "km": listing.get("km"),
        "price_eur": price_cents / 100 if price_cents else None,
        "fuel_type": listing.get("fuel_type"),
        "transmission": listing.get("transmission"),
        "power_hp": listing.get("power_hp"),
        "seller_type": listing.get("seller_type"),
        "seller_country": listing.get("seller_country"),
    }


def _format_comparables(comparable_listings: list[dict]) -> list[dict]:
    """Format comparable listings for the prompt."""
    formatted = []
    for comp in comparable_listings[:10]:  # Limit to 10 comparables for prompt size
        price_cents = comp.get("price_cents")
        formatted.append({
            "title": comp.get("title", ""),
            "year": comp.get("year"),
            "km": comp.get("km"),
            "price_eur": price_cents / 100 if price_cents else None,
            "seller_type": comp.get("seller_type"),
        })
    return formatted


def _empty_result() -> dict:
    return {
        "deal_score": 50,
        "market_avg_price": 0,
        "price_position": "at_market",
        "price_diff_eur": 0,
        "price_diff_pct": 0.0,
        "confidence": "low",
        "reasoning": "Insufficient data to score this deal.",
    }
