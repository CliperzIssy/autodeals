"""Service for scraping seller contact information from listing detail pages."""

import logging
import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scrapling import StealthyFetcher

from app.models.listing import Listing
from app.scrapers.proxy_manager import get_proxy_url

logger = logging.getLogger(__name__)

# Cache phone numbers for 24 hours before re-scraping
PHONE_CACHE_TTL = timedelta(hours=24)

# Common phone number patterns for German listings
PHONE_PATTERN = re.compile(
    r"(?:\+49|0049|0)\s*[\d\s/\-().]{6,20}"
)


async def scrape_contact(listing_id: UUID, db_session: AsyncSession) -> str | None:
    """Scrape the seller phone number from a listing's detail page.

    If the phone number was already scraped within the last 24 hours,
    the cached value is returned without making a new request.

    Args:
        listing_id: UUID of the listing.
        db_session: An async SQLAlchemy session.

    Returns:
        The phone number string, or None if not found.
    """
    # Load listing from DB
    result = await db_session.execute(
        select(Listing).where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()

    if listing is None:
        logger.error("Listing %s not found in database", listing_id)
        return None

    # Check cache: if phone was scraped recently, return it
    if (
        listing.seller_phone
        and listing.seller_phone_scraped_at
        and listing.seller_phone_scraped_at > datetime.now(timezone.utc) - PHONE_CACHE_TTL
    ):
        logger.debug(
            "Returning cached phone for listing %s: %s",
            listing_id, listing.seller_phone,
        )
        return listing.seller_phone

    # Scrape the detail page
    if not listing.source_url:
        logger.warning("Listing %s has no source_url, cannot scrape contact", listing_id)
        return None

    phone = None
    try:
        proxy = get_proxy_url(listing.source)
        logger.info("Fetching detail page for listing %s: %s", listing_id, listing.source_url)

        response = await StealthyFetcher.async_fetch(
            listing.source_url,
            proxy=proxy,
            block_images=True,
        )

        if response is None or response.status != 200:
            status = response.status if response else "None"
            logger.warning(
                "Non-200 response fetching detail page for listing %s: status=%s",
                listing_id, status,
            )
            return None

        if listing.source == "mobile_de":
            phone = _extract_phone_mobile_de(response)
        elif listing.source == "autoscout24":
            phone = _extract_phone_autoscout24(response)
        else:
            logger.warning("Unknown source %s for listing %s", listing.source, listing_id)

    except Exception:
        logger.exception("Failed to scrape contact for listing %s", listing_id)
        return None

    # Update listing with phone number and timestamp
    if phone:
        phone = _normalize_phone(phone)
        listing.seller_phone = phone
        listing.seller_phone_scraped_at = datetime.now(timezone.utc)
        await db_session.commit()
        logger.info("Scraped phone for listing %s: %s", listing_id, phone)
    else:
        # Record the attempt even if no phone was found
        listing.seller_phone_scraped_at = datetime.now(timezone.utc)
        await db_session.commit()
        logger.info("No phone number found for listing %s", listing_id)

    return phone


def _extract_phone_mobile_de(page) -> str | None:
    """Extract phone number from a mobile.de detail page.

    Mobile.de typically hides the phone behind a "Show phone number" button.
    The number may be embedded in a data attribute or revealed via JS.
    """
    # Try direct phone elements
    phone_selectors = [
        'a[href^="tel:"]',
        'span[data-testid="seller-phone"]',
        'div.seller-phone a',
        'a.phone-number',
        'span[class*="phone"]',
    ]
    for selector in phone_selectors:
        el = page.css_first(selector)
        if el:
            # Check href for tel: links
            href = el.attrib.get("href", "")
            if href.startswith("tel:"):
                return href.replace("tel:", "").strip()
            text = el.text(strip=True)
            if text and PHONE_PATTERN.search(text):
                return PHONE_PATTERN.search(text).group(0).strip()

    # Fallback: search the full page text for phone patterns
    body = page.css_first("body")
    if body:
        text = body.text()
        # Look for phone patterns near "Telefon" or "phone" keywords
        phone_section = re.search(
            r"(?:Telefon|Tel\.|Phone|Mobil)[:\s]*(" + PHONE_PATTERN.pattern + r")",
            text,
            re.IGNORECASE,
        )
        if phone_section:
            return phone_section.group(1).strip()

    return None


def _extract_phone_autoscout24(page) -> str | None:
    """Extract phone number from an AutoScout24 detail page.

    AutoScout24 may display the phone number in the dealer info section
    or behind a reveal button.
    """
    # Try direct phone elements
    phone_selectors = [
        'a[href^="tel:"]',
        'span[data-testid="dealer-phone"]',
        'a[class*="phone"]',
        'div[class*="SellerInfo"] a[href^="tel:"]',
        'span[class*="Phone"]',
    ]
    for selector in phone_selectors:
        el = page.css_first(selector)
        if el:
            href = el.attrib.get("href", "")
            if href.startswith("tel:"):
                return href.replace("tel:", "").strip()
            text = el.text(strip=True)
            if text and PHONE_PATTERN.search(text):
                return PHONE_PATTERN.search(text).group(0).strip()

    # Try __NEXT_DATA__ for structured data
    next_data_el = page.css_first("script#__NEXT_DATA__")
    if next_data_el:
        try:
            import json
            data = json.loads(next_data_el.text(strip=True))
            props = data.get("props", {}).get("pageProps", {})

            # Navigate to seller/dealer info
            seller = (
                props.get("listing", {}).get("seller", {})
                or props.get("seller", {})
            )
            phone = seller.get("phone") or seller.get("phoneNumber")
            if phone:
                return str(phone).strip()
        except (ValueError, KeyError, TypeError):
            logger.debug("Could not extract phone from __NEXT_DATA__")

    # Fallback: search page text
    body = page.css_first("body")
    if body:
        text = body.text()
        phone_section = re.search(
            r"(?:Telefon|Tel\.|Phone|Mobil)[:\s]*(" + PHONE_PATTERN.pattern + r")",
            text,
            re.IGNORECASE,
        )
        if phone_section:
            return phone_section.group(1).strip()

    return None


def _normalize_phone(phone: str) -> str:
    """Clean up and normalize a phone number string."""
    # Remove extra whitespace
    phone = re.sub(r"\s+", " ", phone).strip()
    # Remove parentheses around area codes
    phone = phone.replace("(", "").replace(")", "")
    # Normalize common separators
    phone = re.sub(r"[/\-.]", " ", phone)
    # Collapse multiple spaces
    phone = re.sub(r"\s+", " ", phone).strip()
    return phone
