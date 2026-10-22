"""
agents/publisher.py

builds the discord embed (a styled card) and sends it through the webhook.
no llm here, on purpose: the card's fields are copied straight from your answers by code,
so the AI can never alter your details (dates, results, links).
"""

from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

import config
from modes import MODES, card_value
from state import State

TITLE_LIMIT = 256
DESCRIPTION_LIMIT = 4096
FIELD_LIMIT = 1024


def _valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def build_embed(state: State) -> dict:
    mode = MODES[state["mode"]]
    facts = state["facts"]
    labels = {key: label for key, label, _q, _r in mode.fields}

    fields = []
    for key in mode.card_fields:
        value = card_value(mode, key, facts)
        if value:
            fields.append(
                {"name": labels[key], "value": value[:FIELD_LIMIT], "inline": key in mode.inline}
            )

    embed = {
        "title": state["title"][:TITLE_LIMIT],
        "description": state["draft"][:DESCRIPTION_LIMIT],
        "color": mode.color,
        "fields": fields,
        "footer": {"text": config.AUTHOR_NAME},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    link = facts.get("link", "").strip()
    if link and _valid_url(link):
        embed["url"] = link  # makes the card title clickable

    return embed


def render_preview(embed: dict) -> str:
    """plain-text preview of the card, for the terminal."""
    lines = [f"[ {embed['title']} ]", "", embed["description"], ""]
    for f in embed["fields"]:
        lines.append(f"{f['name']}: {f['value']}")
    lines.append(f"\n-- {embed['footer']['text']}")
    if "url" in embed:
        lines.append(f"(title links to {embed['url']})")
    return "\n".join(lines)


def publish(state: State) -> dict:
    embed = build_embed(state)

    if config.DRY_RUN:
        print("\n[publisher] dry run, not sending. this card would go out:\n")
        print(render_preview(embed))
        return {"posted": False}

    if not config.DISCORD_WEBHOOK_URL:
        raise RuntimeError("set DISCORD_WEBHOOK_URL in .env")

    response = requests.post(
        config.DISCORD_WEBHOOK_URL,
        json={
            "embeds": [embed],
            # stops @everyone / @here / role pings from firing even if they appear in the text
            "allowed_mentions": {"parse": []},
        },
        timeout=30,
    )

    # discord answers 204 (no content) on success
    if response.status_code not in (200, 204):
        raise RuntimeError(f"Discord error {response.status_code}: {response.text}")

    print("\n[publisher] posted to Discord")
    return {"posted": True}
