"""
CLI Demo for LangGraph Code Review Agent.
"""

import argparse
from agent import run_code_review


def main():
    parser = argparse.ArgumentParser(description="LangGraph Code Review Demo")
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=2,
        help="Maximum number of rewrite rounds (default 2)",
    )
    args = parser.parse_args()

    sample_function = """
def sort_numbers(nums):
    # Sort a list of numbers in ascending order
    return sorted(nums)
"""

    print("=== Running code review ===")
    final_state = run_code_review(sample_function, max_rounds=args.max_rounds)

    print("\n--- Final Draft Review ---")
    print(final_state["draft_review"])

    print("\n--- Criteria Scores ---")
    for crit, score in final_state["criteria_scores"].items():
        print(f"{crit}: {score}")

    print("\n--- Verdict ---")
    print(final_state["verdict"])


if __name__ == "__main__":
    main()
