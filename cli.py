import argparse
import os
from graph import build_graph
from state import CodeReviewState

def load_code_from_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

def main():
    parser = argparse.ArgumentParser(description="Code Review Agent Demo")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", type=str, help="Path to Python file containing the function.")
    group.add_argument("--code", "-c", type=str, help="Inline code string.")
    parser.add_argument("--max-rounds", "-m", type=int, default=2,
                        help="Maximum number of rewrite rounds (default 2).")
    args = parser.parse_args()

    if args.file:
        code = load_code_from_file(args.file)
    else:
        code = args.code

    state: CodeReviewState = {
        "code": code,
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": "",
        "verdict": "",
        "round": 1,
        "max_rounds": args.max_rounds,
    }

    graph = build_graph()
    final_state = graph.invoke(state)

    print("\n=== Draft Review ===")
    print(final_state["draft_review"])
    print("\n=== Scores ===")
    for crit, score in final_state["criteria_scores"].items():
        print(f"{crit}: {score}")
    print(f"\nWeakest criterion: {final_state['weakest_criterion']}")
    print(f"Verdict: {final_state['verdict']}")
    if final_state["round"] > 1:
        print("\n=== Final Review After Rewrites ===")
        print(final_state["draft_review"])

if __name__ == "__main__":
    main()
