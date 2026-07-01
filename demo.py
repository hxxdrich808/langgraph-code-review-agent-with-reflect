"""
Demo script to run the code review agent on a sample Python file.
"""

import sys

from agent import run_code_review


def main():
    if len(sys.argv) < 2:
        print("Usage: python demo.py <path_to_python_file>")
        return

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    result = run_code_review(code)
    print("\nFinal Review State:")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
