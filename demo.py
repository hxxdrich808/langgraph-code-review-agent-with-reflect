"""
Demo script for the LangGraph code review agent.
"""

from __future__ import annotations

import textwrap

from agent import run_code_review


def main() -> None:
    # Sample function to review
    sample_code = textwrap.dedent(
        """
        def sort_numbers(arr):
            return sorted(arr)
        """
    )

    print("\n=== Running Code Review Agent ===\n")
    final_state = run_code_review(sample_code, max_rounds=2)

    print("\n--- Final State ---")
    print(f"Verdict: {final_state['verdict']}")
    print(f"Rounds performed: {final_state['round']}")
    print("\nDraft Review:")
    print(final_state["draft_review"])
    if final_state["criteria_scores"]:
        print("\nCriteria Scores:")
        for k, v in final_state["criteria_scores"].items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
