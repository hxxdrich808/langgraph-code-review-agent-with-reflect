"""
Demo script for LangGraph Code Review Agent with Reflection.
"""

from __future__ import annotations

import textwrap

from agent import run_code_review


def main() -> None:
    sample_function = """
def sort_numbers(numbers):
    # Sort numbers in ascending order
    sorted_list = sorted(numbers)
    return sorted_list
"""
    code = textwrap.dedent(sample_function)

    print("[bold green]Running Code Review Demo[/]\n")
    final_state = run_code_review(code, max_rounds=2)

    print("\n[bold underline]Final State:[/]")
    print(f"Round: {final_state['round']}")
    print(f"Verdict: {final_state['verdict']}\n")
    print("[bold cyan]Draft Review (after last rewrite if any):[/]\n")
    print(final_state["draft_review"])
    print("\n[bold magenta]Criteria Scores:[/]")
    for k, v in final_state["criteria_scores"].items():
        print(f"  {k}: {v}")
    print(f"\nWeakest Criterion: {final_state['weakest_criterion']}")


if __name__ == "__main__":
    main()
