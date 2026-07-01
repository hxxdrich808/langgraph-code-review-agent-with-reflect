from langgraph import StateGraph, END
from state import CodeReviewState
from nodes.draft_review_node import register as draft_register
from nodes.reflect_node import register as reflect_register
from nodes.rewrite_node import register as rewrite_register

def build_graph() -> StateGraph:
    """
    Build a LangGraph that performs:
    draft_review → reflect → (optional) rewrite → reflect … until verdict == 'ok' or max rounds reached.
    """
    workflow = StateGraph(CodeReviewState)

    # Register nodes
    draft_register(workflow)
    reflect_register(workflow)
    rewrite_register(workflow)

    # Entry point
    workflow.set_entry_point("draft_review")

    # Conditional transition after reflect
    def decide(state: CodeReviewState):
        if state["verdict"] == "ok":
            return END
        elif state["round"] < state.get("max_rounds", 2):
            return "rewrite"
        else:
            return END

    workflow.add_conditional_edges(
        ["reflect"],
        decide,
        {
            "rewrite": "rewrite",
            END: END
        }
    )

    # After rewrite, go back to reflect
    workflow.add_edge("rewrite", "reflect")

    return workflow
