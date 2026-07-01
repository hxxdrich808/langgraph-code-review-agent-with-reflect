import argparse
from graph import build_graph
from state import CodeReviewState

def main():
    parser = argparse.ArgumentParser(description="LangGraph Code Review Agent")
    parser.add_argument("file", help="Path to a Python file containing the function to review")
    args = parser.parse_args()

    with open(args.file, "r") as f:
        code = f.read()

    # Initialize state
    state: CodeReviewState = {
        "code": code,
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": "",
        "verdict": "",
        "round": 1,
        "max_rounds": 2
    }

    graph = build_graph()
    final_state = graph.invoke(state)

    print("\n=== Draft Review ===")
    print(final_state["draft_review"])
    print("\n=== Criteria Scores ===")
    for crit, score in final_state.get("criteria_scores", {}).items():
        print(f"{crit}: {score}")
    print(f"\nWeakest Criterion: {final_state.get('weakest_criterion', '')}")
    print(f"Verdict: {final_state.get('verdict', '')}")

if __name__ == "__main__":
    main()
