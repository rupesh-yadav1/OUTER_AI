# backend/models/dalle.py

import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def dalle_answer(prompt: str, model: str = "dall-e-3") -> str:
    """
    Generate an image via DALL·E and return its URL.
    """
    resp = openai.Image.create(
        model=model,
        prompt=prompt,
        n=1,
        size="1024x1024",
    )
    return resp.data[0].url
