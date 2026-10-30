import logging
import os
from functools import lru_cache

import google.generativeai as genai

from app.config import get_settings

logger = logging.getLogger(__name__)

_MODEL_CANDIDATES = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
)


@lru_cache
def _discover_model_name() -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    genai.configure(api_key=settings.gemini_api_key)
    configured_model = os.environ.get("GEMINI_MODEL", "").strip()

    available_models: list[str] = []
    try:
        for model in genai.list_models():
            methods = set(getattr(model, "supported_generation_methods", []) or [])
            if "generateContent" not in methods:
                continue
            raw_name = getattr(model, "name", "")
            model_name = raw_name.split("/", 1)[1] if raw_name.startswith("models/") else raw_name
            if model_name:
                available_models.append(model_name)
    except Exception:
        logger.exception("Failed to list Gemini models; falling back to configured/default names")

    if available_models:
        preferred: list[str] = []
        if configured_model:
            preferred.append(configured_model)
        preferred.extend(_MODEL_CANDIDATES)

        for candidate in preferred:
            if candidate in available_models:
                logger.info("Using Gemini model: %s", candidate)
                return candidate

        flash_candidate = next((name for name in available_models if "flash" in name), None)
        selected = flash_candidate or available_models[0]
        logger.info("Using discovered Gemini model: %s", selected)
        return selected

    fallback = configured_model or _MODEL_CANDIDATES[0]
    logger.warning("Using fallback Gemini model: %s", fallback)
    return fallback


@lru_cache
def get_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(_discover_model_name())
