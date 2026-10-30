import json
import logging
from pathlib import Path

from app.ai.client import get_model

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "normalize.txt"


def _get_model():
    return get_model()


async def normalize_title(title: str, metadata: dict | None = None) -> dict:
    """Extract structured vehicle info from a raw listing title using Gemini AI.

    Args:
        title: The raw listing title string.
        metadata: Optional additional metadata (year, km, fuel_type, etc.).

    Returns:
        Dict with make, model, generation, variant, sub_variant,
        power_hp, engine_code, notable_features.
    """
    if not title:
        logger.warning("normalize_title called with empty title")
        return _empty_result()

    try:
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt_template.format(
            title=title,
            metadata=json.dumps(metadata or {}, ensure_ascii=False),
        )

        model = _get_model()
        response = model.generate_content(prompt)

        raw_text = response.text.strip()
        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3].strip()

        result = json.loads(raw_text)
        logger.info("Successfully normalized title: %s -> %s", title[:60], result.get("make"))
        return result

    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini JSON response for title '%s': %s", title[:60], e)
        return _empty_result()
    except Exception as e:
        logger.error("Gemini normalization failed for title '%s': %s", title[:60], e)
        return _empty_result()


def _empty_result() -> dict:
    return {
        "make": None,
        "model": None,
        "generation": None,
        "variant": None,
        "sub_variant": None,
        "power_hp": None,
        "engine_code": None,
        "notable_features": [],
    }
