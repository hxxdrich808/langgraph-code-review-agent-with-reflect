"""
CLI Demo for LangGraph Code Review Agent.
"""

import argparse
from pathlib import Path

from agent import run_code_review


def main():
    parser = argparse.ArgumentParser(description="LangGraph Code Review Demo")
    parser.add_argument(
        "file",
        type=Path,
        help="Python file containing the function to review",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=2,
        help="Maximum number of rewrite rounds (default 2)",
    )

    args = parser.parse_args()

    code_text = args.file.read_text(encoding="utf-8")

    final_state = run_code_review(code_text, max_rounds=args.max_rounds)

    print("\n=== Final Review ===")
    print(final_state["draft_review"])
    print("\n=== Scores ===")
    for k, v in final_state["criteria_scores"].items():
        print(f"{k}: {v}")
    print(f"\nVerdict: {final_state['verdict']}")
    if final_state["verdict"] == "needs_revision":
        print("Review could not be finalized within the allowed rounds.")


if __name__ == "__main__":
    main()
