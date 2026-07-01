#!/usr/bin/env python3
"""
Demo CLI for LangGraph Code Review Agent with Reflection.
Usage:
    python demo.py <path_to_python_file>
"""

import argparse
from pathlib import Path

from agent import run_code_review


def main() -> None:
    parser = argparse.ArgumentParser(description="LangGraph Code Review Demo")
    parser.add_argument(
        "file",
        type=Path,
        help="Path to the Python file containing the function to review.",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        raise FileNotFoundError(f"File {args.file} does not exist.")

    code_text = args.file.read_text(encoding="utf-8")

    print("\n=== Running Code Review ===\n")
    final_state = run_code_review(code_text)

    print("\n=== Final State ===")
    print(f"Verdict: {final_state['verdict']}")
    print(f"Weakest Criterion: {final_state['weakest_criterion']}")
    print("Criteria Scores:")
    for k, v in final_state["criteria_scores"].items():
        print(f"  {k}: {v}")
    print("\nFinal Draft Review:\n")
    print(final_state["draft_review"])


if __name__ == "__main__":
    main()
