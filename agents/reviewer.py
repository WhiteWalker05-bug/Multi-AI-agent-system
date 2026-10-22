"""
agents/reviewer.py

the reviewer agent. how strict it is depends on the mode.

strict modes (achievement, announcement):
  code:  length, and every number in the post must appear in your input
  llm:   every claim backed by your input, no exaggeration, tone, first line
light modes (discussion, free):
  code:  length
  llm:   tone, first line, no invented statistics, does not drift from your points

input:  state["mode"], state["draft"], state["title"], state["facts"]
output: state["approved_by_ai"], state["feedback"], state["attempts"]
"""

import re

from pydantic import BaseModel, Field

from llm import llm
from modes import MODES, facts_text
from state import State


class Verdict(BaseModel):
    approved: bool
    issues: str = Field(description="if rejected, a short list of specific fixes. empty if approved")


STRICT_PROMPT = """you review Discord posts of type "{label}". you are also the fact-checker.

the facts the author gave (the only things that may be stated as true):
{facts}

the draft:
{draft}

reject the draft if any of these is true:
- it states something that is not supported by the facts (invented detail, name, outcome or result)
- it exaggerates or inflates anything beyond what the facts say
- it sounds generic or robotic
- the first line is weak
- the tone is boastful or pushy instead of genuine

if the draft is good, approve it. do not nitpick. when you reject, quote the exact problem sentence."""

LIGHT_PROMPT = """you review Discord posts of type "{label}" before they are published.

what the author wanted to say:
{facts}

the draft:
{draft}

reject the draft if any of these is true:
- it sounds generic or robotic
- the first line is weak
- it states invented statistics or facts as if they were true (opinions and questions are fine)
- it ignores or contradicts what the author wanted to say
- the tone is rude, spammy or pushy

if the draft is good, approve it. do not nitpick. when you reject, quote the exact problem sentence."""

structured_llm = llm.with_structured_output(Verdict)


def _numbers(text: str) -> set[str]:
    found = re.findall(r"\d[\d,]*\.?\d*", text)
    cleaned = {n.replace(",", "").rstrip(".") for n in found}
    return {str(int(n)) if n.isdigit() else n for n in cleaned}  # "05" and "5" count as the same


def reviewer_agent(state: State) -> dict:
    mode = MODES[state["mode"]]
    draft = state["draft"]
    facts = facts_text(mode, state["facts"])
    problems = []

    # rules checked by code
    words = len(draft.split())
    if words > mode.max_words:
        problems.append(f"too long: {words} words, the limit is {mode.max_words}")

    if mode.strict:
        unknown = sorted(_numbers(state.get("title", "") + " " + draft) - _numbers(facts))
        if unknown:
            problems.append(
                "these numbers are not in the author's input, remove or correct them: " + ", ".join(unknown)
            )

    # quality (and fact-check, in strict modes) by the llm
    prompt = STRICT_PROMPT if mode.strict else LIGHT_PROMPT
    verdict = structured_llm.invoke(prompt.format(label=mode.label, facts=facts, draft=draft))
    if not verdict.approved and verdict.issues:
        problems.append(verdict.issues)

    attempts = state.get("attempts", 0) + 1
    approved = not problems

    print(f"\n[reviewer] review {attempts}: {'approved' if approved else 'needs changes'}")
    for p in problems:
        print(f"  - {p}")

    return {
        "approved_by_ai": approved,
        "feedback": "\n".join(problems),
        "attempts": attempts,
    }
