# backend/models/groq.py

import os
import json
import requests
import datetime
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def groq_answer(user_msg: str, model_id: str = "llama-3.1-8b-instant") -> str:
    try:
        user_msg = user_msg.encode('utf-8', errors='ignore').decode('utf-8')
        now = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
        system_prompt = (
            f"You are a helpful assistant. "
            f"The current system date and time is: {now}. "
            f"Use this information to answer any date or time related questions accurately."
        )

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "Groq API error. Please try again later."


def groq_stream(user_msg: str, model_id: str = "llama-3.1-8b-instant"):
    try:
        user_msg = user_msg.encode('utf-8', errors='ignore').decode('utf-8')
        now = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
        system_prompt = (
            f"You are a helpful assistant. "
            f"The current system date and time is: {now}. "
            f"Use this information to answer any date or time related questions accurately."
        )

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": True
        }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        with requests.post(GROQ_URL, json=payload, headers=headers, stream=True, timeout=30) as response:
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data:"):
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data)
                        delta = parsed["choices"][0]["delta"]
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except Exception as e:
                        logger.warning(f"Groq stream parse error: {e}")

    except Exception as e:
        logger.error(f"Groq streaming error: {e}")
        yield "[Error] Groq streaming failed."
