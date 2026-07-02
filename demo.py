"""
Demo script for LangGraph Code Review Agent.
"""

from __future__ import annotations

import argparse
from textwrap import dedent

from agent import run_code_review, rprint


def sample_sort_numbers() -> str:
    """
    Sample function to demonstrate the code review agent.
    Returns the source code as a string.
    """
    return dedent(
        """\
        def sort_numbers(numbers: list[int]) -> list[int]:
            \"\"\"Sorts a list of numbers in ascending order.\"\"\"
            # Using built-in sorted for simplicity
            return sorted(numbers)
        """
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="LangGraph Code Review Agent Demo")
    parser.add_argument(
        "--code",
        type=str,
        help="Path to a Python file containing the code to review. If omitted, a sample function is used.",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=2,
        help="Maximum number of rewrite rounds (default: 2)",
    )
    args = parser.parse_args()

    if args.code:
        with open(args.code, "r", encoding="utf-8") as f:
            code_str = f.read()
    else:
        code_str = sample_sort_numbers()

    rprint("[bold underline]Running Code Review Agent...[/]")
    final_state = run_code_review(code_str, max_rounds=args.max_rounds)

    rprint("\n[bold green]Final State:[/]")
    rprint(f"Verdict: {final_state['verdict']}")
    rprint(f"Round: {final_state['round']} / {final_state['max_rounds']}")
    rprint("Scores:")
    for k, v in final_state["criteria_scores"].items():
        rprint(f"  {k}: {v}")

    rprint("\n[bold cyan]Final Review:[/]\n" + final_state["draft_review"])


if __name__ == "__main__":
    main()
