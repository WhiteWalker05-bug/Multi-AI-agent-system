"""
state.py

the shared memory of the system. every agent reads from it and writes back to it.
"""

from typing import TypedDict


class State(TypedDict):
    mode: str             # post type: achievement, announcement, discussion or free
    topic: str            # short summary (taken from the first answer)
    facts: dict[str, str]  # your answers
    angles: list[str]     # idea agent: 3 post angles
    angle: str            # the one you picked
    title: str            # writer agent: headline for the card
    draft: str            # writer agent: the post text
    approved_by_ai: bool  # reviewer verdict
    feedback: str         # reviewer notes (used for the rewrite and shown at approval)
    attempts: int         # how many reviews so far
    approved: bool        # you, at the approval step
    posted: bool          # publisher
