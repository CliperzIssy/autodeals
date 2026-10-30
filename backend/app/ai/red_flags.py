import json
import logging
from pathlib import Path

from app.ai.client import get_model

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "red_flags.txt"


def _get_model():
    return get_model()


async def detect_red_flags(description: str) -> dict:
    """Analyze a German car listing description for red flags.

    Args:
        description: The German-language listing description.

    Returns:
        Dict with flags (list), overall_risk, and clean_signals.
    """
    if not description or not description.strip():
        logger.info("detect_red_flags called with empty description, returning empty result")
        return _empty_result()

    try:
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt_template.format(description=description)

        model = _get_model()
        response = model.generate_content(prompt)

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3].strip()

        result = json.loads(raw_text)

        # Validate expected keys
        result.setdefault("flags", [])
        result.setdefault("overall_risk", "low")
        result.setdefault("clean_signals", [])

        flag_count = len(result["flags"])
        logger.info(
            "Red flag analysis complete: %d flags found, overall_risk=%s",
            flag_count,
            result["overall_risk"],
        )
        return result

    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini JSON response for red flags: %s", e)
        return _empty_result()
    except Exception as e:
        logger.error("Gemini red flag detection failed: %s", e)
        return _empty_result()


def _empty_result() -> dict:
    return {
        "flags": [],
        "overall_risk": "low",
        "clean_signals": [],
    }
