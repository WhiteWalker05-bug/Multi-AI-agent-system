"""
graph.py

wires the agents together.

START -> ideas -> picker (you choose) -> writer -> reviewer
reviewer -> writer      if it needs changes and we have tries left
reviewer -> approval    if good, or out of tries (you see the reviewer's note)
approval (you say yes/no) -> publish or END
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

import config
from agents.approval import approval
from agents.ideas import ideas_agent
from agents.picker import picker
from agents.publisher import publish
from agents.reviewer import reviewer_agent
from agents.writer import writer_agent
from state import State


def after_review(state: State):
    if not state["approved_by_ai"] and state["attempts"] < config.MAX_REVIEWS:
        return "writer"
    return "approval"


def after_approval(state: State):
    return "publish" if state["approved"] else END


def build_graph():
    graph = StateGraph(State)
    retry = RetryPolicy(max_attempts=3)

    graph.add_node("ideas", ideas_agent, retry_policy=retry)
    graph.add_node("picker", picker)
    graph.add_node("writer", writer_agent, retry_policy=retry)
    graph.add_node("reviewer", reviewer_agent, retry_policy=retry)
    graph.add_node("approval", approval)
    graph.add_node("publish", publish)  # no retry: a retry could post twice

    graph.add_edge(START, "ideas")
    graph.add_edge("ideas", "picker")
    graph.add_edge("picker", "writer")
    graph.add_edge("writer", "reviewer")
    graph.add_conditional_edges("reviewer", after_review, ["writer", "approval"])
    graph.add_conditional_edges("approval", after_approval, ["publish", END])
    graph.add_edge("publish", END)

    return graph.compile(checkpointer=InMemorySaver())
