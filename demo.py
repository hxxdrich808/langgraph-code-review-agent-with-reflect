"""
CLI Demo for LangGraph Code Review Agent.
"""

import argparse
import os
import sys

from agent import run_code_review


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a code review with reflection and optional rewrites."
    )
    parser.add_argument(
        "source",
        help=(
            "Python function code as a string or path to a .py file containing the "
            "function. If a file is provided, its contents will be used."
        ),
    )
    args = parser.parse_args()

    # Load code from file or use raw string
    if os.path.isfile(args.source):
        with open(args.source, encoding="utf-8") as f:
            code_text = f.read()
    else:
        code_text = args.source

    print("\n[bold green]Running Code Review...[/]\n")
    final_state = run_code_review(code_text)

    print("\n[bold underline]Final Draft Review:[/]")
    print(final_state["draft_review"])
    print("\n[bold underline]Scores and Verdict:[/]")
    for k, v in final_state["criteria_scores"].items():
        print(f"  {k}: {v}")
    print(f"Verdict: {final_state['verdict']}")


if __name__ == "__main__":
    main()
