"""
agents/picker.py

human step 1: you choose which angle to write.
interrupt() pauses the graph until you answer.
"""

from langgraph.types import interrupt

from state import State


def picker(state: State) -> dict:
    answer = interrupt({"type": "pick", "angles": state["angles"]})

    try:
        index = int(str(answer).strip()) - 1
        angle = state["angles"][index]
    except (ValueError, IndexError):
        angle = state["angles"][0]  # bad input: fall back to the first angle

    return {"angle": angle}
