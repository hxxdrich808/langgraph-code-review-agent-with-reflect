"""
Unit tests for agent state transitions.
"""

import pytest

from agent import (
    CodeReviewState,
    build_graph,
    run_code_review,
)

# Sample minimal function to review
SAMPLE_CODE = """
def sort_numbers(arr):
    return sorted(arr)
"""


@pytest.fixture
def initial_state() -> CodeReviewState:
    return {
        "code": SAMPLE_CODE,
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": "",
        "verdict": "needs_revision",
        "round": 0,
        "max_rounds": 2,
    }


def test_draft_review_node():
    graph = build_graph()
    state = initial_state()
    # Invoke draft_review node directly
    new_state = graph.nodes["draft_review"](state)
    assert isinstance(new_state.get("draft_review"), str)
    assert new_state["round"] == 0


def test_reflect_and_rewrite_flow():
    final_state = run_code_review(SAMPLE_CODE, max_rounds=1)
    # After one round of rewrite (if needed) the verdict should be either ok or needs_revision
    assert "draft_review" in final_state
    assert isinstance(final_state["criteria_scores"], dict)
    assert final_state["verdict"] in ("ok", "needs_revision")
    # If needs_revision, round must not exceed max_rounds
    if final_state["verdict"] == "needs_revision":
        assert final_state["round"] <= 1


def test_max_rounds_limit():
    final_state = run_code_review(SAMPLE_CODE, max_rounds=0)
    # With zero rounds allowed, should end after initial reflect
    assert final_state["round"] == 0
    assert final_state["verdict"] in ("ok", "needs_revision")
