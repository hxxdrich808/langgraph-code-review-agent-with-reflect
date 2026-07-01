import pytest
from unittest.mock import MagicMock, patch
from state import CodeReviewState
from graph import build_graph

@pytest.fixture
def mock_llm():
    """Mock ChatOpenAI to return predictable responses."""
    with patch("nodes.draft_review_node.llm") as mock:
        mock.invoke.return_value.content = (
            "- Uses sorted() which is efficient.\n"
            "- No type hints provided.\n"
            "- Handles empty lists implicitly.\n"
            "- Variable names follow PEP8."
        )
        yield mock

    with patch("nodes.reflect_node.llm") as mock:
        mock.invoke.return_value.content = (
            '{'
            '  "criteria_scores": {'
            '    "PEP8 compliance": 5,'
            '    "Type hints presence and correctness": 3,'
            '    "Edge case handling": 4,'
            '    "Naming conventions": 5'
            '  },'
            '  "weakest_criterion": "Type hints presence and correctness",'
            '  "verdict": "needs_revision"'
            '}'
        )
        yield mock

    with patch("nodes.rewrite_node.llm") as mock:
        mock.invoke.return_value.content = (
            "- Uses sorted() which is efficient.\n"
            "- Provides type hints for input and output.\n"
            "- Handles empty lists implicitly.\n"
            "- Variable names follow PEP8."
        )
        yield mock

def test_graph_flow(mock_llm):
    """Test that the graph loops correctly until max rounds or ok verdict."""
    # Initial state
    state: CodeReviewState = {
        "code": "def sort_numbers(nums): return sorted(nums)",
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": "",
        "verdict": "",
        "round": 1,
        "max_rounds": 2,
    }

    graph = build_graph()
    final_state = graph.invoke(state)

    # After first draft and reflect, verdict should be needs_revision
    assert final_state["verdict"] == "needs_revision"
    # Round should have incremented after rewrite
    assert final_state["round"] == 2
    # Draft review should contain rewritten type hints section
    assert "Provides type hints" in final_state["draft_review"]
    # Since round equals max_rounds, graph should end with verdict still needs_revision
    assert final_state["verdict"] == "needs_revision"

def test_no_rewrite_needed():
    """If verdict is ok on first reflect, no rewrite occurs."""
    with patch("nodes.draft_review_node.llm") as mock_draft:
        mock_draft.invoke.return_value.content = (
            "- Uses sorted() which is efficient.\n"
            "- Provides type hints for input and output.\n"
            "- Handles empty lists implicitly.\n"
            "- Variable names follow PEP8."
        )
    with patch("nodes.reflect_node.llm") as mock_reflect:
        mock_reflect.invoke.return_value.content = (
            '{'
            '  "criteria_scores": {'
            '    "PEP8 compliance": 9,'
            '    "Type hints presence and correctness": 10,'
            '    "Edge case handling": 9,'
            '    "Naming conventions": 9'
            '  },'
            '  "weakest_criterion": "PEP8 compliance",'
            '  "verdict": "ok"'
            '}'
        )

    state: CodeReviewState = {
        "code": "def sort_numbers(nums): return sorted(nums)",
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": "",
        "verdict": "",
        "round": 1,
        "max_rounds": 2,
    }

    graph = build_graph()
    final_state = graph.invoke(state)

    # No rewrite should have happened
    assert final_state["round"] == 1
    assert final_state["verdict"] == "ok"
    assert "Provides type hints" in final_state["draft_review"]

def test_rewrite_section_extraction():
    """Ensure that the rewrite node correctly replaces only the weak section."""
    state: CodeReviewState = {
        "code": "def sort_numbers(nums): return sorted(nums)",
        "draft_review": (
            "- Uses sorted() which is efficient.\n"
            "- No type hints provided.\n"
            "- Handles empty lists implicitly.\n"
            "- Variable names follow PEP8."
        ),
        "criteria_scores": {},
        "weakest_criterion": "No type hints provided.",
        "verdict": "",
        "round": 1,
        "max_rounds": 2,
    }

    with patch("nodes.rewrite_node.llm") as mock_llm:
        mock_llm.invoke.return_value.content = (
            "- Uses sorted() which is efficient.\n"
            "- Provides type hints for input and output.\n"
            "- Handles empty lists implicitly.\n"
            "- Variable names follow PEP8."
        )
        new_state = graph.invoke(state)

    assert "Provides type hints" in new_state["draft_review"]
    assert "No type hints provided." not in new_state["draft_review"]

def test_invalid_json_in_reflect():
    """Reflect node should raise ValueError if LLM returns invalid JSON."""
    with patch("nodes.reflect_node.llm") as mock_llm:
        mock_llm.invoke.return_value.content = "Not a JSON"

        state: CodeReviewState = {
            "code": "",
            "draft_review": "",
            "criteria_scores": {},
            "weakest_criterion": "",
            "verdict": "",
            "round": 1,
            "max_rounds": 2,
        }

        with pytest.raises(ValueError):
            graph.invoke(state)
