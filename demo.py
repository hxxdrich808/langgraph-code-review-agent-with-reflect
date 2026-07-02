"""
Demo of the LangGraph code review agent.
"""

from __future__ import annotations

import textwrap

from agent import run_code_review


def sort_numbers(numbers):
    """Sort a list of numbers in ascending order."""
    # Using built-in sorted for simplicity
    return sorted(numbers)


if __name__ == "__main__":
    sample_code = textwrap.dedent(
        """
        def sort_numbers(numbers):
            \"\"\"Sort a list of numbers in ascending order.\"\"\"
            # Using built-in sorted for simplicity
            return sorted(numbers)
        """
    )

    print("\n=== Running code review demo ===\n")
    result = run_code_review(sample_code, max_rounds=2)

    print("\n--- Final Review ---")
    print(result["draft_review"])
    print("\n--- Scores ---")
    for k, v in result["criteria_scores"].items():
        print(f"{k}: {v}")
    print(f"\nVerdict: {result['verdict']}")
    print(f"Weakest criterion: {result['weakest_criterion']}")
    print(f"Rounds performed: {result['round']}")
