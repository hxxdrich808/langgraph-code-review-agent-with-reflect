from langgraph import StateGraph, END
from typing import Dict, Any
from nodes import draft_review, reflect, rewrite
from state import CodeReviewState

def build_graph() -> StateGraph:
    """
    Build the LangGraph workflow for code review with reflection.
    Returns a compiled graph ready to invoke.
    """
    graph = StateGraph(CodeReviewState)

    # Add nodes
    graph.add_node("draft", draft_review)
    graph.add_node("reflect", reflect)
    graph.add_node("rewrite", rewrite)

    # Define transitions
    def should_rewrite(state: Dict[str, Any]) -> bool:
        return state["verdict"] == "needs_revision" and state["round"] < state["max_rounds"]

    graph.set_entry_point("draft")
    graph.add_edge("draft", "reflect")
    graph.add_conditional_edges(
        "reflect",
        lambda s: END if s["verdict"] == "ok" else ("rewrite" if should_rewrite(s) else END),
    )
    graph.add_edge("rewrite", "reflect")

    # Compile the graph to get an invokable object
    return graph.compile()
