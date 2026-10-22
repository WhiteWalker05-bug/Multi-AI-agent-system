"""
agents/writer.py

the writer agent. drafts the post, or rewrites it using the reviewer's feedback.
it may only use what you typed in. if voice.txt exists, it is used as a style reference.

input:  state["mode"], state["facts"], state["angle"], state["draft"], state["feedback"]
output: state["title"], state["draft"]
"""

from pathlib import Path

from pydantic import BaseModel, Field

import config
from llm import llm
from modes import MODES, facts_text
from state import State


class Post(BaseModel):
    title: str = Field(description="short headline for the card, under 80 characters")
    text: str = Field(description="the post text")


PROMPT = """you write Discord posts for {name}, {role}, for {audience}.
post type: {label}. {brief}

the author's input below is the ONLY source of facts:
{facts}

angle to write: {angle}

rules:
- never invent numbers, names, dates, tools or outcomes
- do not exaggerate. no words like "revolutionary", "massive" or "huge" unless the input says so
- if the input is thin for this angle, write a shorter post instead of making things up
- start with a hook that grabs attention
- under {max_words} words, short paragraphs, friendly casual Discord tone
- no hashtags. light markdown is fine (**bold**, bullet lists)
- do not use @everyone, @here or @mentions
{voice}{rewrite}"""


structured_llm = llm.with_structured_output(Post)


def _voice_block() -> str:
    path = Path("voice.txt")
    if path.exists() and path.read_text().strip():
        return f"\nmatch the style of these past posts:\n{path.read_text().strip()}\n"
    return ""


def writer_agent(state: State) -> dict:
    mode = MODES[state["mode"]]

    rewrite = ""
    if state.get("feedback") and state.get("draft"):
        rewrite = (
            f"\nthis is your previous draft:\n{state['draft']}\n\n"
            f"a reviewer asked for these fixes:\n{state['feedback']}\n"
            "rewrite the post and fix them.\n"
        )

    result = structured_llm.invoke(
        PROMPT.format(
            name=config.AUTHOR_NAME,
            role=config.AUTHOR_ROLE,
            audience=config.AUDIENCE,
            label=mode.label,
            brief=mode.brief,
            facts=facts_text(mode, state["facts"]),
            angle=state["angle"],
            max_words=mode.max_words,
            voice=_voice_block(),
            rewrite=rewrite,
        )
    )
    print("\n[writer] draft ready" if not rewrite else "\n[writer] rewrite ready")
    return {"title": result.title.strip(), "draft": result.text.strip()}
