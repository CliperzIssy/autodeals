"""URL builders for mobile.de and AutoScout24 search pages."""

import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# mobile.de make/model IDs (top 20+ makes)
# ---------------------------------------------------------------------------
MOBILE_DE_MAKE_IDS: dict[str, int] = {
    "audi": 1900,
    "bmw": 3500,
    "citroen": 4600,
    "fiat": 6600,
    "ford": 7000,
    "honda": 9000,
    "hyundai": 9600,
    "jaguar": 10200,
    "kia": 10600,
    "land rover": 11200,
    "mazda": 12300,
    "mercedes-benz": 12600,
    "mini": 13200,
    "mitsubishi": 13400,
    "nissan": 13800,
    "opel": 14600,
    "peugeot": 15600,
    "porsche": 16200,
    "renault": 17200,
    "seat": 18700,
    "skoda": 19000,
    "suzuki": 20200,
    "tesla": 20800,
    "toyota": 21000,
    "volkswagen": 22900,
    "volvo": 23100,
}

MOBILE_DE_MODEL_IDS: dict[str, dict[str, int]] = {
    "bmw": {"3-series": 21, "5-series": 23, "x3": 45, "x5": 47},
    "volkswagen": {"golf": 10, "polo": 25, "tiguan": 48, "passat": 20},
    "mercedes-benz": {"c-class": 12, "e-class": 14, "a-class": 2, "glc": 60},
    "audi": {"a3": 2, "a4": 3, "a6": 5, "q5": 32, "q7": 33},
    "toyota": {"corolla": 10, "rav4": 36, "yaris": 44, "camry": 5},
}

MOBILE_DE_FUEL_MAP: dict[str, str] = {
    "petrol": "PETROL",
    "diesel": "DIESEL",
    "electric": "ELECTRICITY",
    "hybrid": "HYBRID",
    "lpg": "LPG",
    "cng": "CNG",
}

MOBILE_DE_TRANSMISSION_MAP: dict[str, str] = {
    "automatic": "AUTOMATIC",
    "manual": "MANUAL_GEAR",
}

# ---------------------------------------------------------------------------
# AutoScout24 make/model slugs (top 20+ makes)
# ---------------------------------------------------------------------------
AS24_MAKE_SLUGS: dict[str, str] = {
    "audi": "audi",
    "bmw": "bmw",
    "citroen": "citroen",
    "cupra": "cupra",
    "fiat": "fiat",
    "ford": "ford",
    "honda": "honda",
    "hyundai": "hyundai",
    "jaguar": "jaguar",
    "kia": "kia",
    "land rover": "land-rover",
    "mazda": "mazda",
    "mercedes-benz": "mercedes-benz",
    "mini": "mini",
    "mitsubishi": "mitsubishi",
    "nissan": "nissan",
    "opel": "opel",
    "peugeot": "peugeot",
    "porsche": "porsche",
    "renault": "renault",
    "seat": "seat",
    "skoda": "skoda",
    "suzuki": "suzuki",
    "tesla": "tesla",
    "toyota": "toyota",
    "volkswagen": "volkswagen",
    "volvo": "volvo",
}

AS24_MODEL_SLUGS: dict[str, dict[str, str]] = {
    "bmw": {"3-series": "3er", "5-series": "5er", "x3": "x3", "x5": "x5"},
    "volkswagen": {"golf": "golf", "polo": "polo", "tiguan": "tiguan", "passat": "passat"},
    "mercedes-benz": {"c-class": "c-klasse", "e-class": "e-klasse", "a-class": "a-klasse", "glc": "glc"},
    "audi": {"a3": "a3", "a4": "a4", "a6": "a6", "q5": "q5", "q7": "q7"},
    "toyota": {"corolla": "corolla", "rav4": "rav4", "yaris": "yaris", "camry": "camry"},
}

AS24_FUEL_MAP: dict[str, str] = {
    "petrol": "B",
    "diesel": "D",
    "electric": "E",
    "hybrid": "2",
    "lpg": "L",
    "cng": "C",
}

AS24_TRANSMISSION_MAP: dict[str, str] = {
    "automatic": "A",
    "manual": "M",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(name: str) -> str:
    """Lower-case and strip a make/model name for dictionary lookups."""
    return name.strip().lower() if name else ""


def get_mobile_de_make_id(make: str) -> int | None:
    """Return the mobile.de numeric make ID, or None if unknown."""
    return MOBILE_DE_MAKE_IDS.get(_normalize(make))


def get_mobile_de_model_id(make: str, model: str) -> int | None:
    """Return the mobile.de numeric model ID, or None if unknown."""
    models = MOBILE_DE_MODEL_IDS.get(_normalize(make), {})
    return models.get(_normalize(model))


def get_as24_make_slug(make: str) -> str | None:
    """Return the AutoScout24 URL slug for a make."""
    return AS24_MAKE_SLUGS.get(_normalize(make))


def get_as24_model_slug(make: str, model: str) -> str | None:
    """Return the AutoScout24 URL slug for a model."""
    models = AS24_MODEL_SLUGS.get(_normalize(make), {})
    return models.get(_normalize(model))


# ---------------------------------------------------------------------------
# URL Builders
# ---------------------------------------------------------------------------

def build_mobile_de_url(
    make: str,
    model: str | None = None,
    variant: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    km_min: int | None = None,
    km_max: int | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    fuel_type: str | None = None,
    transmission: str | None = None,
    page: int = 1,
) -> str:
    """Build a mobile.de search URL from filter parameters.

    Prices are expected in **cents** and will be converted to whole euros for
    the URL query string.
    """
    base = "https://suchen.mobile.de/fahrzeuge/search.html"
    params: dict[str, str | int] = {}

    make_id = get_mobile_de_make_id(make)
    if make_id is not None:
        params["makeModelVariant1.makeId"] = make_id
    else:
        logger.warning("Unknown mobile.de make: %s", make)
        params["makeModelVariant1.searchInFreetext"] = make

    if model:
        model_id = get_mobile_de_model_id(make, model)
        if model_id is not None:
            params["makeModelVariant1.modelId"] = model_id
        else:
            params["makeModelVariant1.modelDescription"] = model

    if variant:
        params["makeModelVariant1.modelDescription"] = variant

    if year_min is not None:
        params["minFirstRegistrationDate"] = year_min
    if year_max is not None:
        params["maxFirstRegistrationDate"] = year_max
    if km_min is not None:
        params["minMileage"] = km_min
    if km_max is not None:
        params["maxMileage"] = km_max
    if price_min is not None:
        params["minPrice"] = price_min // 100
    if price_max is not None:
        params["maxPrice"] = price_max // 100

    if fuel_type:
        mapped = MOBILE_DE_FUEL_MAP.get(_normalize(fuel_type))
        if mapped:
            params["fuels"] = mapped

    if transmission:
        mapped = MOBILE_DE_TRANSMISSION_MAP.get(_normalize(transmission))
        if mapped:
            params["transmissions"] = mapped

    params["pageNumber"] = page
    params["lang"] = "en"
    params["isSearchRequest"] = "true"

    url = f"{base}?{urlencode(params, doseq=True)}"
    logger.debug("Built mobile.de URL: %s", url)
    return url


def build_autoscout24_url(
    make: str,
    model: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    km_min: int | None = None,
    km_max: int | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    fuel_type: str | None = None,
    transmission: str | None = None,
    countries: list[str] | None = None,
    page: int = 1,
) -> str:
    """Build an AutoScout24 search URL from filter parameters.

    Prices are expected in **cents** and will be converted to whole euros.
    """
    make_slug = get_as24_make_slug(make) or _normalize(make)
    model_slug = get_as24_model_slug(make, model) if model else None

    if model_slug:
        path = f"/lst/{make_slug}/{model_slug}"
    else:
        path = f"/lst/{make_slug}"

    base = f"https://www.autoscout24.com{path}"

    params: dict[str, str | int] = {}

    if year_min is not None:
        params["fregfrom"] = year_min
    if year_max is not None:
        params["fregto"] = year_max
    if km_min is not None:
        params["kmfrom"] = km_min
    if km_max is not None:
        params["kmto"] = km_max
    if price_min is not None:
        params["pricefrom"] = price_min // 100
    if price_max is not None:
        params["priceto"] = price_max // 100

    if fuel_type:
        mapped = AS24_FUEL_MAP.get(_normalize(fuel_type))
        if mapped:
            params["fuel"] = mapped

    if transmission:
        mapped = AS24_TRANSMISSION_MAP.get(_normalize(transmission))
        if mapped:
            params["gear"] = mapped

    if countries:
        params["cy"] = ",".join(c.upper() for c in countries)

    if page > 1:
        params["page"] = page

    params["sort"] = "standard"
    params["desc"] = 0
    params["atype"] = "C"  # cars only

    url = f"{base}?{urlencode(params, doseq=True)}"
    logger.debug("Built AutoScout24 URL: %s", url)
    return url
