"""
Demo CLI for LangGraph Code Review Agent.
"""

import argparse
from agent import run_code_review


def main():
    parser = argparse.ArgumentParser(description="Run code review on a Python function.")
    parser.add_argument(
        "code_file",
        type=str,
        help="Path to a .py file containing the function to review.",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=2,
        help="Maximum number of rewrite rounds (default: 2).",
    )

    args = parser.parse_args()

    with open(args.code_file, "r", encoding="utf-8") as f:
        code = f.read()

    final_state = run_code_review(code, max_rounds=args.max_rounds)

    print("\n=== Final Review ===")
    print(final_state["draft_review"])


if __name__ == "__main__":
    main()
