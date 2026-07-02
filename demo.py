"""
Command‑line demo for the LangGraph code review agent.
"""

import argparse
import textwrap
from pathlib import Path

from agent import run_code_review


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a code review with reflection on a Python function."
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        default=None,
        help="Path to a .py file containing the function. If omitted, stdin is used.",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=None,
        help="Maximum number of rewrite rounds (default: 2).",
    )
    return parser.parse_args()


def read_code(path: Path | None) -> str:
    if path:
        return path.read_text(encoding="utf-8")
    # Read from stdin
    print("Enter Python code (end with EOF):")
    return "".join(textwrap.dedent(line) for line in iter(input, ""))


def main() -> None:
    args = parse_args()
    code = read_code(args.file)

    final_state = run_code_review(code, max_rounds=args.max_rounds)

    print("\n=== Final Review ===")
    print(final_state["draft_review"])
    print("\n=== Scores ===")
    for k, v in final_state["criteria_scores"].items():
        print(f"  {k}: {v}")
    print(f"\nWeakest criterion: {final_state['weakest_criterion']}")
    print(f"Verdict: {final_state['verdict']}")
    print(f"Rounds performed: {final_state['round']} / {final_state['max_rounds']}")


if __name__ == "__main__":
    main()
