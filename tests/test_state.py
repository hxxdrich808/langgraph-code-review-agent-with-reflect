import pytest
from code_review_agent import CodeReviewState, draft_review_node, reflect_node, rewrite_node


def test_initial_state():
    state = {
        "code": "def f(): pass",
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": None,
        "verdict": "",
        "round": 1,
        "max_rounds": 2,
    }
    # Draft review node should populate draft_review
    result = draft_review_node(state)
    assert isinstance(result["draft_review"], str) and len(result["draft_review"]) > 0


def test_reflect_scores():
    state = {
        "code": "",
        "draft_review": "- Good naming\n- Missing type hints",
        "criteria_scores": {},
        "weakest_criterion": None,
        "verdict": "",
        "round": 1,
        "max_rounds": 2,
    }
    # Mock LLM by patching llm.invoke
    from unittest.mock import patch

    mock_response = '{"pep8":7,"type_hints":5,"edge_cases":8,"naming":9,"weakest_criterion":"type_hints","verdict":"needs_revision"}'
    with patch("code_review_agent.llm.invoke") as mock_inv:
        mock_inv.return_value.content = mock_response
        result = reflect_node(state)
        assert state["criteria_scores"]["type_hints"] == 5
        assert state["weakest_criterion"] == "type_hints"
        assert state["verdict"] == "needs_revision"


def test_rewrite_increments_round():
    state = {
        "code": "",
        "draft_review": "- Good naming",
        "criteria_scores": {},
        "weakest_criterion": "naming",
        "verdict": "needs_revision",
        "round": 1,
        "max_rounds": 2,
    }
    from unittest.mock import patch

    mock_response = "- Improved naming conventions"
    with patch("code_review_agent.llm.invoke") as mock_inv:
        mock_inv.return_value.content = mock_response
        result = rewrite_node(state)
        assert state["draft_review"] == "- Improved naming conventions"
        assert state["round"] == 2


def test_graph_termination():
    from code_review_agent import build_graph

    graph = build_graph()
    app = graph.compile()

    # Prepare a state that will trigger termination after max rounds
    state = {
        "code": "",
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": None,
        "verdict": "",
        "round": 1,
        "max_rounds": 2,
    }

    # Mock LLM responses to force needs_revision until max rounds
    from unittest.mock import patch

    mock_draft = "- Issue"
    mock_reflect = '{"pep8":5,"type_hints":4,"edge_cases":6,"naming":7,"weakest_criterion":"pep8","verdict":"needs_revision"}'
    with patch("code_review_agent.llm.invoke") as mock_inv:
        # Sequence: draft -> reflect -> rewrite -> reflect
        mock_inv.side_effect = [
            type('Resp', (), {"content": mock_draft}),
            type('Resp', (), {"content": mock_reflect}),
            type('Resp', (), {"content": mock_draft}),
            type('Resp', (), {"content": mock_reflect}),
        ]
        final_state = app.invoke(state)
    # After two rounds, verdict should still be needs_revision but round == 3
    assert state["round"] == 3
    assert state["verdict"] == "needs_revision"
