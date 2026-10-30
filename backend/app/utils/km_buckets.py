"""Mileage (km) bucketing utilities for listing aggregation."""

import logging

logger = logging.getLogger(__name__)

# (lower_bound_inclusive, upper_bound_exclusive_or_None, label)
KM_BUCKETS: list[tuple[int, int | None, str]] = [
    (0, 50_000, "0-50k"),
    (50_000, 100_000, "50-100k"),
    (100_000, 150_000, "100-150k"),
    (150_000, None, "150k+"),
]


def get_bucket(km: int) -> str:
    """Return the human-readable bucket label for a given mileage.

    Parameters
    ----------
    km:
        Mileage in kilometres.  Negative values are clamped to 0.

    Returns
    -------
    str
        The matching bucket label, e.g. ``"50-100k"``.
    """
    if km < 0:
        km = 0

    for lower, upper, label in KM_BUCKETS:
        if upper is None:
            # Last (open-ended) bucket
            if km >= lower:
                return label
        else:
            if lower <= km < upper:
                return label

    # Fallback – should never happen given the bucket definitions above.
    logger.warning("No bucket matched for km=%d, defaulting to last bucket", km)
    return KM_BUCKETS[-1][2]


def group_by_bucket(listings: list) -> dict[str, list]:
    """Group a list of listing objects or dicts by mileage bucket.

    Each element must either expose a ``.km`` attribute or be a dict with a
    ``"km"`` key.  Listings without a km value are placed in a special
    ``"unknown"`` bucket.

    Returns
    -------
    dict[str, list]
        Mapping from bucket label to a list of listings in that bucket.
    """
    buckets: dict[str, list] = {label: [] for _, _, label in KM_BUCKETS}
    buckets["unknown"] = []

    for listing in listings:
        km: int | None
        if isinstance(listing, dict):
            km = listing.get("km")
        else:
            km = getattr(listing, "km", None)

        if km is None:
            buckets["unknown"].append(listing)
        else:
            bucket_label = get_bucket(km)
            buckets[bucket_label].append(listing)

    # Remove empty buckets for cleaner output
    return {k: v for k, v in buckets.items() if v}
