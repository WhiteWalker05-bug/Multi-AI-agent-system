"""
agents/approval.py

human step 2: nothing is sent unless you type yes.
"""

from langgraph.types import interrupt

from agents.publisher import build_embed
from state import State


def approval(state: State) -> dict:
    answer = interrupt(
        {
            "type": "approve",
            "embed": build_embed(state),
            "review_note": state.get("feedback", ""),
        }
    )
    return {"approved": str(answer).strip().lower() in ("y", "yes")}
