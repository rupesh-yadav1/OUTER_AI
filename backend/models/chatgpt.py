import os
import datetime
import logging
from dotenv import load_dotenv
from openai import OpenAI

# ─── Load environment & configure logger ──────────────────────────────────
load_dotenv()
logger = logging.getLogger(__name__)

# ─── Sanitize API key (replace any non-breaking hyphens) ─────────────────
_raw_api_key = os.getenv("OPENAI_API_KEY", "")
_api_key = _raw_api_key.replace("\u2011", "-")

# ─── Initialize OpenAI client ─────────────────────────────────────────────
client = OpenAI(api_key=_api_key)

def chatgpt_answer(user_msg: str, model_id: str = "gpt-4o") -> str:
    """
    Synchronous (non-streaming) ChatGPT response
    """
    if not user_msg or not user_msg.strip():
        return "Please provide a message to send to the assistant."
    
    try:
        cleaned = user_msg.strip().encode("utf-8", errors="ignore").decode("utf-8")
        now = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
        system_prompt = (
            f"You are a helpful assistant. "
            f"The current system date and time is: {now}. "
            f"Answer any time/date-related questions using this information."
        )

        resp = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": cleaned},
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        content = resp.choices[0].message.content or ""
        if content.strip():
            return content.strip()
        
        logger.warning("ChatGPT returned empty response (model=%s)", model_id)
        return "I couldn't generate a response. Please try rephrasing your question."

    except Exception as e:
        error_msg = str(e).lower()
        if "authentication" in error_msg or "api key" in error_msg:
            logger.error("OpenAI Authentication error: %s", e)
            return "Authentication failed. Please check your API key configuration."
        elif "rate limit" in error_msg or "quota" in error_msg:
            logger.error("OpenAI Rate limit error: %s", e)
            return "Rate limit exceeded. Please try again in a moment."
        elif "connection" in error_msg or "network" in error_msg or "timeout" in error_msg:
            logger.error("OpenAI Connection error: %s", e)
            return "I'm having trouble connecting to the AI service. Please check your internet connection and try again."
        elif "invalid" in error_msg and "model" in error_msg:
            logger.error("Invalid model error: %s", e)
            return f"The model '{model_id}' is not available. Please try with a different model."
        else:
            logger.exception("Unexpected error in chatgpt_answer")
            return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."


def chatgpt_stream(user_msg: str, model_id: str = "gpt-4o"):
    """
    Streaming ChatGPT response using OpenAI stream=True
    Yields one chunk at a time.
    """
    if not user_msg or not user_msg.strip():
        yield "Please provide a message to send to the assistant."
        return

    try:
        cleaned = user_msg.strip().encode("utf-8", errors="ignore").decode("utf-8")
        now = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
        system_prompt = (
            f"You are a helpful assistant. "
            f"The current system date and time is: {now}. "
            f"Answer any time/date-related questions using this information."
        )

        stream = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": cleaned}
            ],
            temperature=0.7,
            max_tokens=1024,
            stream=True
        )

        for chunk in stream:
            # Correct access to ChoiceDelta's content attribute
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content

    except Exception as e:
        logger.error("Streaming error: %s", e)
        yield f"\n[Error]: {str(e)}"
