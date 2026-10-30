"""Dutch BPM (vehicle purchase tax) calculator – 2025 rules.

References:
    https://www.belastingdienst.nl/wps/wcm/connect/nl/auto-en-vervoer/
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CO2 brackets for petrol/LPG/CNG (grammes/km -> euro per g/km)
# Dutch 2025 BPM CO2 table for petrol vehicles.
# Each entry: (upper_bound_exclusive_or_None, base_amount, rate_per_gram)
# The rate applies to each g/km *above* the previous bracket's upper bound.
# ---------------------------------------------------------------------------
CO2_BRACKETS: list[tuple[int | None, int, float]] = [
    # (co2 up-to, cumulative base, marginal rate EUR per g/km)
    (79, 0, 0.0),           # 0-78 g/km: zero BPM
    (107, 0, 79.0),         # 79-106 g/km
    (155, 2_212, 122.0),    # 107-154 g/km
    (170, 8_068, 192.0),    # 155-169 g/km
    (190, 10_948, 266.0),   # 170-189 g/km
    (None, 16_268, 411.0),  # 190+ g/km
]

# Diesel surcharge: extra EUR per g/km above 72 g/km
DIESEL_SURCHARGE_THRESHOLD = 72
DIESEL_SURCHARGE_RATE = 91.0  # EUR per g/km

# ---------------------------------------------------------------------------
# Depreciation table – percentage of original BPM remaining by age.
# Dutch tax authority publishes a fixed table; values below are the 2025
# edition simplified to monthly steps.
# ---------------------------------------------------------------------------
DEPRECIATION_TABLE: list[tuple[int, float]] = [
    # (age_months_upper, remaining_pct)
    (1, 0.98),
    (2, 0.94),
    (3, 0.90),
    (6, 0.84),
    (9, 0.78),
    (12, 0.72),
    (18, 0.62),
    (24, 0.53),
    (30, 0.46),
    (36, 0.40),
    (42, 0.35),
    (48, 0.31),
    (54, 0.27),
    (60, 0.24),
    (66, 0.21),
    (72, 0.19),
    (84, 0.15),
    (96, 0.12),
    (108, 0.10),
    (120, 0.08),
    (144, 0.06),
    (168, 0.04),
    (192, 0.03),
    (216, 0.02),
    (240, 0.01),
]


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def calculate_co2_bpm(co2_grams_per_km: int) -> int:
    """Return the gross BPM in euros based on CO2 emissions (petrol table).

    This uses the 2025 bracket table for petrol / LPG / CNG vehicles.
    """
    if co2_grams_per_km <= 0:
        return 0

    prev_upper = 0
    for upper, base, rate in CO2_BRACKETS:
        if upper is None:
            # Open-ended last bracket
            extra = co2_grams_per_km - prev_upper
            return int(base + extra * rate)
        if co2_grams_per_km < upper:
            extra = co2_grams_per_km - prev_upper
            return int(base + extra * rate)
        prev_upper = upper

    # Should not reach here, but return max bracket as safety.
    _, base, rate = CO2_BRACKETS[-1]
    return int(base + (co2_grams_per_km - prev_upper) * rate)


def diesel_surcharge(co2_grams_per_km: int) -> int:
    """Return the diesel surcharge in euros.

    Applied on top of the normal CO2-based BPM for diesel vehicles.
    """
    if co2_grams_per_km <= DIESEL_SURCHARGE_THRESHOLD:
        return 0
    extra_grams = co2_grams_per_km - DIESEL_SURCHARGE_THRESHOLD
    return int(extra_grams * DIESEL_SURCHARGE_RATE)


def get_depreciation_percentage(age_months: int) -> float:
    """Return the remaining BPM fraction for a vehicle of the given age.

    Returns a value between 0.0 and 1.0 representing the fraction of the
    original (new-car) BPM that still applies.
    """
    if age_months <= 0:
        return 1.0

    for upper_months, pct in DEPRECIATION_TABLE:
        if age_months <= upper_months:
            return pct

    # Older than the last entry in the table – use the minimum.
    return DEPRECIATION_TABLE[-1][1]


def estimate_bpm(
    co2_grams_per_km: int,
    age_months: int,
    fuel_type: str = "petrol",
) -> int:
    """Estimate the BPM payable in euros for importing a used vehicle.

    Parameters
    ----------
    co2_grams_per_km:
        WLTP CO2 value.
    age_months:
        Vehicle age in months from first registration.
    fuel_type:
        ``"petrol"``, ``"diesel"``, ``"electric"``, ``"hybrid"``, ``"lpg"``, ``"cng"``.

    Returns
    -------
    int
        Estimated BPM in whole euros.
    """
    fuel_lower = fuel_type.strip().lower() if fuel_type else "petrol"

    if fuel_lower == "electric":
        return 0

    gross_bpm = calculate_co2_bpm(co2_grams_per_km)

    if fuel_lower == "diesel":
        gross_bpm += diesel_surcharge(co2_grams_per_km)

    remaining = get_depreciation_percentage(age_months)
    net_bpm = int(gross_bpm * remaining)

    logger.debug(
        "BPM estimate: co2=%d fuel=%s age=%d months | gross=%d remaining=%.2f net=%d",
        co2_grams_per_km,
        fuel_lower,
        age_months,
        gross_bpm,
        remaining,
        net_bpm,
    )
    return net_bpm


# ---------------------------------------------------------------------------
# Total cost helper
# ---------------------------------------------------------------------------

def estimate_total_cost(
    price_cents: int,
    bpm_euros: int,
    transport_euros: int = 400,
) -> int:
    """Return estimated total landed cost in **cents**.

    ``price_cents`` is the vehicle purchase price in euro cents.
    ``bpm_euros`` and ``transport_euros`` are in whole euros and will be
    converted internally.
    """
    bpm_cents = bpm_euros * 100
    transport_cents = transport_euros * 100
    total = price_cents + bpm_cents + transport_cents
    return total


# ---------------------------------------------------------------------------
# Rough CO2 estimator when official value is unavailable
# ---------------------------------------------------------------------------

# Average g CO2/km per litre of engine displacement, by fuel type and era.
# These are rough heuristics — real values depend on engine tech, weight, etc.
_PETROL_FACTOR: dict[str, float] = {
    "old": 0.135,   # pre-2010
    "mid": 0.120,   # 2010-2017
    "new": 0.105,   # 2018+
}
_DIESEL_FACTOR: dict[str, float] = {
    "old": 0.130,
    "mid": 0.110,
    "new": 0.095,
}


def _era(year: int | None) -> str:
    if year is None or year < 2010:
        return "old"
    if year < 2018:
        return "mid"
    return "new"


def estimate_co2_from_engine(
    engine_cc: int,
    fuel_type: str = "petrol",
    year: int | None = None,
) -> int:
    """Rough CO2 g/km estimate based on engine displacement.

    This is a **very** rough heuristic used only when the official CO2 value
    is not available from the listing.

    Parameters
    ----------
    engine_cc:
        Engine displacement in cubic centimetres.
    fuel_type:
        ``"petrol"`` or ``"diesel"``.
    year:
        First-registration year (used to pick an era factor).

    Returns
    -------
    int
        Estimated CO2 in grams per km.
    """
    if engine_cc <= 0:
        logger.warning("Invalid engine_cc=%d, returning 0", engine_cc)
        return 0

    fuel_lower = fuel_type.strip().lower() if fuel_type else "petrol"
    era = _era(year)

    if fuel_lower == "diesel":
        factor = _DIESEL_FACTOR[era]
    else:
        factor = _PETROL_FACTOR[era]

    co2 = int(engine_cc * factor)
    logger.debug(
        "Estimated CO2: engine=%dcc fuel=%s year=%s era=%s factor=%.3f -> %d g/km",
        engine_cc,
        fuel_lower,
        year,
        era,
        factor,
        co2,
    )
    return co2
