"""
agents/ideas.py

the idea agent. proposes 3 different ways to write your post.

input:  state["mode"], state["facts"]
output: state["angles"]
"""

from pydantic import BaseModel, Field

import config
from llm import llm
from modes import MODES, facts_text
from state import State


class Angles(BaseModel):
    angles: list[str] = Field(
        description="exactly 3 post angles. each is one line: the angle type, then a specific headline"
    )


PROMPT = """you help {name}, {role}, write Discord posts for {audience}.
post type: {label}.

here is what the author told you:
{facts}

propose exactly 3 different ways to write this post. each is one line: the angle type, then a specific headline.
good angle types: {angle_types}.
only suggest angles the input can honestly support. do not write the post itself."""

structured_llm = llm.with_structured_output(Angles)


def ideas_agent(state: State) -> dict:
    mode = MODES[state["mode"]]
    result = structured_llm.invoke(
        PROMPT.format(
            name=config.AUTHOR_NAME,
            role=config.AUTHOR_ROLE,
            audience=config.AUDIENCE,
            label=mode.label,
            facts=facts_text(mode, state["facts"]),
            angle_types=mode.angle_types,
        )
    )
    print("\n[idea agent] angles ready")
    return {"angles": result.angles[:3], "attempts": 0, "feedback": ""}
