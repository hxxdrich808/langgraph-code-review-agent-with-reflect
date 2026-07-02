"""
Unit tests for the LangGraph Code Review Agent.
"""

from unittest.mock import patch, MagicMock

import pytest

from agent import run_code_review, CodeReviewState


@pytest.fixture
def sample_code():
    return """
def add(a, b):
    return a + b
"""


def mock_llm_with_scores(*args, **kwargs):
    """Return a ReflectionResult with low scores to trigger rewrite."""
    from agent import ReflectionResult

    # Simulate first round: all below threshold
    if kwargs.get("state", {}).get("round") == 0:
        return ReflectionResult(
            pep8=5,
            type_hints=6,
            edge_cases=4,
            naming=7,
            weakest_criterion="edge_cases",
            verdict="needs_revision",
            justification="low scores",
        )
    # Second round: all above threshold
    else:
        return ReflectionResult(
            pep8=9,
            type_hints=9,
            edge_cases=9,
            naming=9,
            weakest_criterion="pep8",
            verdict="ok",
            justification="good",
        )


def test_run_code_review_max_rounds(monkeypatch, sample_code):
    # Patch LLM calls to return controlled results
    def mock_chain_invoke(self, inputs):
        # Determine which node is being called by inspecting the prompt name
        if "draft" in self.prompt.template[0][1]:
            # Draft review node returns a simple string
            return MagicMock(content="• Good style\n• Missing type hints")
        elif "reflect" in self.prompt.template[0][1]:
            # Reflect node uses our mock_llm_with_scores
            state = inputs.get("state", {})
            return mock_llm_with_scores(state=state)
        else:
            # Rewrite node returns a rewritten review
            return MagicMock(content="• Improved edge case handling")

    monkeypatch.setattr(
        "langchain_core.prompts.ChatPromptTemplate.invoke",
        mock_chain_invoke,
    )

    final_state: CodeReviewState = run_code_review(sample_code, max_rounds=2)

    assert final_state["round"] == 1
    assert final_state["verdict"] == "ok"
    assert final_state["criteria_scores"]["edge_cases"] == 9
