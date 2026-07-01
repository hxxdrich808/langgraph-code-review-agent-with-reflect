"""
Simple CLI demo for the LangGraph code review agent.
"""

import argparse
from textwrap import dedent

from agent import run_code_review


def sort_numbers(numbers):
    """Sort a list of numbers in ascending order."""
    # Using built-in sorted function for simplicity
    return sorted(numbers)


def main():
    parser = argparse.ArgumentParser(
        description="Demo: Run code review on a sample function."
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=2,
        help="Maximum number of rewrite rounds (default 2)",
    )
    args = parser.parse_args()

    # Sample code to review
    sample_code = dedent("""
    def sort_numbers(numbers):
        \"\"\"Sort a list of numbers in ascending order.\"\"\"
        # Using built-in sorted function for simplicity
        return sorted(numbers)
    """)

    result = run_code_review(sample_code, max_rounds=args.max_rounds)

    print("\n=== Draft Review ===")
    print(result["draft_review"])
    print("\n=== Scores ===")
    for k, v in result["criteria_scores"].items():
        print(f"{k}: {v}")
    print(f"\nWeakest criterion: {result['weakest_criterion']}")
    print(f"Verdict: {result['verdict']}")
    if result["round"] > 0:
        print("\n=== Rewritten Review ===")
        print(result["draft_review"])
    else:
        print("\nNo rewrite performed.")


if __name__ == "__main__":
    main()
