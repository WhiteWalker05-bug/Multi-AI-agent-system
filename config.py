"""
config.py

loads everything from .env in one place.
"""

import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

AUTHOR_NAME = os.getenv("AUTHOR_NAME", "the author")
AUTHOR_ROLE = os.getenv("AUTHOR_ROLE", "a community member")
AUDIENCE = os.getenv("AUDIENCE", "people in my Discord server")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# safe default: never send unless this is explicitly set to false
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"

MAX_REVIEWS = 2  # review once, allow one rewrite, then hand the draft to the human
