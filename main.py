"""
main.py

run it with:
  uv run main.py
it asks what you want to post, asks a few questions, then walks through the agents.
"""

import sys
import uuid

from langgraph.types import Command

import config
from agents.publisher import render_preview
from graph import build_graph
from modes import MODES, validate


def choose_mode():
    keys = list(MODES)
    print("what do you want to post?\n")
    for i, key in enumerate(keys, start=1):
        print(f"  {i}. {MODES[key].label}: {MODES[key].description}")
    while True:
        answer = input("\nnumber: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(keys):
            return MODES[keys[int(answer) - 1]]
        print(f"  type a number from 1 to {len(keys)}")


def collect_facts(mode) -> dict:
    print(f"\n{mode.label}. press enter to skip the optional questions.\n")
    facts = {}
    for key, _label, question, required in mode.fields:
        while True:
            value = input(f"{question}: ").strip()
            if not value and required:
                print("  this one is required.")
                continue
            error = validate(mode, key, value)
            if error:
                print(f"  {error}")
                continue
            break
        if value:
            facts[key] = value
    return facts


def main():
    if not config.GOOGLE_API_KEY:
        sys.exit("GOOGLE_API_KEY is missing. copy .env.example to .env and fill it in.")

    mode = choose_mode()
    facts = collect_facts(mode)

    app = build_graph()
    run_config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    result = app.invoke({"mode": mode.key, "topic": facts["what"], "facts": facts}, run_config)

    # the graph pauses twice: once to pick an angle, once to approve the card
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value

        if payload["type"] == "pick":
            print("\nchoose an angle:")
            for i, angle in enumerate(payload["angles"], start=1):
                print(f"  {i}. {angle}")
            answer = input("\nnumber (1-3): ")

        else:  # approve
            print("\n" + "=" * 60)
            print(render_preview(payload["embed"]))
            print("=" * 60)
            if payload["review_note"]:
                print(f"\nreviewer still has concerns:\n{payload['review_note']}")
            where = "DRY RUN, nothing will be sent" if config.DRY_RUN else "this will be sent to your Discord channel"
            answer = input(f"\npublish? ({where}) (yes/no): ")

        result = app.invoke(Command(resume=answer), run_config)

    print(f"\ndone. posted: {result.get('posted', False)}")


if __name__ == "__main__":
    main()
