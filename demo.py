import subprocess
import sys

def run_demo():
    # Example function to review
    code = """
def sort_numbers(nums):
    \"\"\"Return a sorted list of numbers.\"\"\"
    return sorted(nums)
"""
    # Write to temp file
    with open("temp_example.py", "w") as f:
        f.write(code)

    # Run the agent via CLI
    subprocess.run([sys.executable, "-m", "code_review_agent", "--file", "temp_example.py"])

if __name__ == "__main__":
    run_demo()
