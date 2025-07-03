import os
import logging
import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

# Initialize global singleton
_CLIENT: genai.Client | None = None
MODEL_ID = "gemini-2.5-flash"  # Updated model

def _client() -> genai.Client:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = genai.Client(api_key=API_KEY)
    return _CLIENT

def gemini_answer(prompt: str, model_id: str = MODEL_ID) -> str:
    prompt = prompt.encode('utf-8', errors='ignore').decode('utf-8')
    now = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    system_preface = (
        f"You are a helpful assistant. "
        f"The current system date and time is: {now}.\n\n"
    )
    resp = _client().models.generate_content(
        model=model_id,
        contents=system_preface + prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=1024
        )
    )
    if resp.candidates and resp.candidates[0].content.parts:
        return resp.candidates[0].content.parts[0].text.strip()
    return "I couldn't generate a response. Please try again."

def gemini_stream(prompt: str, model_id: str = MODEL_ID):
    prompt = prompt.encode('utf-8', errors='ignore').decode('utf-8')
    now = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    system_preface = (
        f"You are a helpful assistant. "
        f"The current system date and time is: {now}.\n\n"
    )
    chat = _client().chats.create(model=model_id)
    response = chat.send_message(system_preface + prompt, stream=True)
    for chunk in response:
        text = chunk.text.strip()
        if text:
            yield text
