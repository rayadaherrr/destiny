"""
The Week 1 goal: one API call that works.

Run with:  uv run python hello_ai.py
"""
from google import genai
from google.genai import types

import config

client = genai.Client(api_key=config.API_KEY)

response = client.models.generate_content(
    model=config.MODEL,
    contents="Say hello in one short sentence.",
    config=types.GenerateContentConfig(temperature=config.TEMPERATURE),
)

print(response.text)
