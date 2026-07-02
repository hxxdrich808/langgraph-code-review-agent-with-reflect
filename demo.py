"""
Demo script for LangGraph Code Review Agent.
"""

from agent import run_code_review


def main() -> None:
    # Sample function to review
    code_to_review = """
def sort_numbers(numbers):
    \"\"\"Sort a list of numbers in ascending order.\"\"\"
    return sorted(numbers)
"""

    print("=== Running Code Review Demo ===\n")
    final_state = run_code_review(code_to_review)

    print("\n=== Final State ===")
    print(f"Verdict: {final_state['verdict']}")
    print(f"Round: {final_state['round']} / {final_state['max_rounds']}")
    print("Scores:")
    for k, v in final_state["criteria_scores"].items():
        print(f"  {k}: {v}")
    print("\nFinal Draft Review:\n")
    print(final_state["draft_review"])


if __name__ == "__main__":
    main()
