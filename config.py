"""
Central configuration.

Everything you change often lives here, not scattered across the code.
This is the minimal version of the "Centralized Configuration" the final
project requires.
"""
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Explicit path: without it, load_dotenv also searches parent folders and may
# pick up a .env that is not yours, hiding the error.
load_dotenv(Path(__file__).parent / ".env")

# Model responses can contain any character. Without this, an emoji in a
# reply crashes the script on a Windows console.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

# The SDK warns about automatic function calling on every request, even when
# no tools are involved. That is noise, so silence this logger only.
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

API_KEY = os.getenv("GOOGLE_API_KEY")

# The "-latest" aliases always point at the newest stable release, so the code
# is not pinned to a model that gets retired.
MODEL = "gemini-flash-lite-latest"

TEMPERATURE = 0.7
