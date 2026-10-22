"""
modes.py

the post types. each mode decides:
  - which questions you are asked
  - what the writer is told to do
  - how strict the reviewer is
  - which of your answers appear as fields on the card

add a new mode by adding one entry to MODES. nothing else needs to change.
"""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import config

# (key, label shown on the card, question asked in the terminal, required?)
LINK = ("link", "Link", "Link to share (optional)", False)


@dataclass(frozen=True)
class Mode:
    key: str
    label: str
    description: str
    fields: tuple        # the questions
    card_fields: tuple   # which answers show as fields on the card
    inline: tuple        # which card fields sit side by side
    strict: bool         # True = every number and claim must be backed by your input
    max_words: int
    color: int           # card accent color
    angle_types: str     # what the idea agent should offer
    brief: str           # extra instructions for the writer


MODES = {
    "achievement": Mode(
        key="achievement",
        label="Achievement",
        description="share something you did (strictly fact-checked)",
        fields=(
            ("what", "What I did", "What did you achieve or do?", True),
            ("result", "Result", "Result or numbers (optional)", False),
            ("tools", "Tools", "Tools or skills used (optional)", False),
            ("when", "When", "When did it happen? (optional)", False),
            LINK,
            ("notes", "Notes", "Anything else: challenges, lessons, people to thank (optional)", False),
        ),
        card_fields=("what", "result", "tools", "when", "link"),
        inline=("tools", "when"),
        strict=True,
        max_words=200,
        color=0x5865F2,
        angle_types="milestone announcement, what I learned, behind the scenes, thank-you to the people who helped",
        brief=(
            "the post shares one of the author's real achievements.\n"
            "- write in first person\n"
            "- the card already shows What I did, Result, Tools and When as separate fields, so do not just "
            "repeat them. tell the human side: why it mattered, what was hard, what the author learned, who "
            "helped, but only as far as the input and notes support\n"
            "- end with a question or an invitation so people want to reply"
        ),
    ),
    "announcement": Mode(
        key="announcement",
        label="Announcement or event",
        description="tell the server about an event or news",
        fields=(
            ("what", "What", "What are you announcing?", True),
            ("when", "When", "Date and time as YYYY-MM-DD HH:MM, in your timezone (optional)", False),
            ("where", "Where", "Where? a place, voice channel or link (optional)", False),
            ("details", "Details", "Key details: who it is for, what to bring, how to join (optional)", False),
            LINK,
        ),
        card_fields=("when", "where", "link"),
        inline=("when", "where"),
        strict=True,
        max_words=150,
        color=0x57F287,
        angle_types="straightforward announcement, exciting teaser, friendly reminder with the practical details, why you should come",
        brief=(
            "the post announces an event or news to the community.\n"
            "- be clear about what it is, who it is for and how to take part\n"
            "- the card already shows the date, time and place, so do not repeat the date or time in the text\n"
            "- end with a clear call to action, for example asking people to react if they are coming"
        ),
    ),
    "discussion": Mode(
        key="discussion",
        label="Discussion question",
        description="start a conversation or ask the community something",
        fields=(
            ("what", "Topic", "What do you want to ask or discuss?", True),
            ("context", "Context", "Background or context (optional)", False),
            LINK,
        ),
        card_fields=("link",),
        inline=(),
        strict=False,
        max_words=120,
        color=0xFEE75C,
        angle_types="open question, share your experience, this-or-that, a friendly hot take",
        brief=(
            "the post starts a conversation in the community.\n"
            "- ask one clear question\n"
            "- give brief context from what the author wrote, then invite replies\n"
            "- opinions are fine as the author's own view, but never state invented statistics or facts"
        ),
    ),
    "free": Mode(
        key="free",
        label="Free post",
        description="any message: you type the main points, it polishes them",
        fields=(
            ("what", "Points", "What do you want to say? type the main points", True),
            LINK,
        ),
        card_fields=("link",),
        inline=(),
        strict=False,
        max_words=200,
        color=0x99AAB5,
        angle_types="short and punchy, story style, a list of key points",
        brief=(
            "the post is the author's own message, polished.\n"
            "- keep the author's meaning and main points\n"
            "- do not add new claims, numbers or details the author did not give\n"
            "- fix the flow and tone, and keep it natural"
        ),
    ),
}


# ---------- dates (announcement mode) ----------

def _when_datetime(raw: str) -> datetime:
    dt = datetime.strptime(raw.strip(), "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=ZoneInfo(config.TIMEZONE))


def when_plain(raw: str) -> str:
    """readable date for the prompts, e.g. Thursday 5 November 2026, 18:00 (UTC)"""
    dt = _when_datetime(raw)
    return f"{dt:%A} {dt.day} {dt:%B %Y}, {dt:%H:%M} ({config.TIMEZONE})"


def when_discord(raw: str) -> str:
    """discord timestamp tags: each member sees the time in their own timezone"""
    ts = int(_when_datetime(raw).timestamp())
    return f"<t:{ts}:F> (<t:{ts}:R>)"


def validate(mode: Mode, key: str, value: str) -> str | None:
    """returns an error message if the answer is not usable, otherwise None."""
    if mode.key == "announcement" and key == "when" and value:
        try:
            dt = _when_datetime(value)
        except ValueError:
            return "use the format YYYY-MM-DD HH:MM, for example 2026-11-05 18:00"
        except ZoneInfoNotFoundError:
            return f"TIMEZONE '{config.TIMEZONE}' in .env is not a valid timezone name"
        if dt < datetime.now(dt.tzinfo):
            return "that date is in the past"
    return None


# ---------- helpers used by the agents ----------

def facts_text(mode: Mode, facts: dict) -> str:
    """your answers as plain text, for putting into prompts."""
    lines = []
    for key, label, _question, _required in mode.fields:
        value = facts.get(key)
        if not value:
            continue
        if mode.key == "announcement" and key == "when":
            value = when_plain(value)
        lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def card_value(mode: Mode, key: str, facts: dict) -> str:
    """what a card field shows. dates become discord timestamps."""
    value = facts.get(key, "").strip()
    if value and mode.key == "announcement" and key == "when":
        return when_discord(value)
    return value
