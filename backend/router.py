# backend/router.py

import os
import logging
from typing import Dict, Set, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv

# ─── Load env & configure logging ─────────────────────────────────────────
load_dotenv()
logger = logging.getLogger(__name__)

# ─── Initialize OpenAI client with ASCII-only API key ────────────────────
_raw_api_key = os.getenv("OPENAI_API_KEY", "")
_api_key = _raw_api_key.replace("\u2011", "-")  # replace any non-breaking hyphens
client = OpenAI(api_key=_api_key)

# ─── Whitelist of supported model IDs ─────────────────────────────────────
VALID_MODELS: Dict[str, Set[str]] = {
    "chatgpt": {"gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"},
    "gemini": {
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2.0-flash-preview-image-generation",
    },
    "groq": {"llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mistral-saba-24b"},
}

DEFAULT_MODEL: Dict[str, str] = {
    "chatgpt": "gpt-4o",
    "gemini": "gemini-1.5-flash",
    "groq": "llama-3.1-8b-instant",
}


def _sanitize(reply: str) -> Optional[Tuple[str, str]]:
    """
    Parse "provider=model_id" replies and ensure they match our whitelist.
    """
    try:
        reply = reply.lower().strip()
        if "=" not in reply:
            return None
        provider, model_id = map(str.strip, reply.split("=", 1))
        if provider in VALID_MODELS and model_id in VALID_MODELS[provider]:
            return provider, model_id
    except Exception as e:
        logger.error("Error sanitizing router response: %s", e)
    return None


def choose_model(question: str) -> Tuple[str, str]:
    """
    Route the user's question to the appropriate model.
    Falls back to chatgpt|gpt-4o on any error.
    """
    try:
        # Normalize input
        cleaned = question.encode("utf-8", errors="ignore").decode("utf-8").lower()
        logger.info("Routing question: %s", cleaned[:50])

        # 1) Rule-based shortcuts
        if any(k in cleaned for k in ["image", "photo", "draw", "jpg", "png", "visual"]):
            return "gemini", "gemini-2.0-flash-preview-image-generation"
        if any(k in cleaned for k in ["speed", "latency", "fast", "math", "calculate"]):
            return "groq", "llama-3.1-8b-instant"
        if any(k in cleaned for k in ["code", "program", "debug", "class", "function"]):
            return "chatgpt", "gpt-4o"
        if any(k in cleaned for k in ["hi", "hello", "hey", "good morning", "good evening"]):
            return "groq", "llama-3.1-8b-instant"

        # 2) LLM-based smart routing
        prompt = f"""Return one line in the form provider=model_id

Allowed values:
chatgpt: gpt-4 | gpt-4o | gpt-4o-mini | gpt-3.5-turbo | gpt-4-turbo
gemini: gemini-1.5-pro | gemini-1.5-flash | gemini-2.0-flash-preview-image-generation
groq: llama-3.3-70b-versatile | llama-3.1-8b-instant | mistral-saba-24b

Guidelines:
- Use gpt-4 or gpt-4o for complex reasoning, detailed explanations, and coding.
- Use gemini-2.0-flash-preview-image-generation for image requests.
- Use gemini-1.5-flash for fast text generation.
- Use groq for speed-sensitive or math tasks.

User task: "{cleaned}"
""".strip()

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=20,
        )
        
        raw = response.choices[0].message.content
        if raw:
            raw = raw.strip()
            logger.info("Router LLM raw → %s", raw)

            parsed = _sanitize(raw)
            if parsed:
                logger.info("Smart routing → %s|%s", parsed[0], parsed[1])
                return parsed

    except Exception as e:
        error_msg = str(e).lower()
        
        # Log specific error types for debugging
        if "authentication" in error_msg or "api key" in error_msg:
            logger.error("Router authentication error: %s", e)
        elif "rate limit" in error_msg or "quota" in error_msg:
            logger.error("Router rate limit error: %s", e)
        elif "connection" in error_msg or "network" in error_msg:
            logger.error("Router connection error: %s", e)
        elif "invalid" in error_msg and "model" in error_msg:
            logger.error("Router invalid model error: %s", e)
        else:
            logger.error("Router general error: %s", e)

    # 3) Final fallback
    fallback = ("chatgpt", DEFAULT_MODEL["chatgpt"])
    logger.info("Fallback routing → %s|%s", fallback[0], fallback[1])
    return fallback