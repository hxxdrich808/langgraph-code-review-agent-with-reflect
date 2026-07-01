from langgraph import StateGraph
from state import CodeReviewState
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

def draft_review(state: CodeReviewState) -> dict:
    """
    Generate an initial review of 3–6 concise points.
    """
    code = state["code"]
    prompt = f"""
You are a senior software engineer reviewing the following Python function.

```python
{code}
```

Provide an initial review consisting of 3 to 6 concise points. Do not include any JSON or formatting, just plain text.
"""
    response = llm.invoke(prompt)
    return {"draft_review": response.content.strip()}

def register(graph: StateGraph):
    graph.add_node("draft_review", draft_review)


from langgraph import StateGraph
from state import CodeReviewState
from langchain_openai import ChatOpenAI
import json

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

def critic(state: CodeReviewState) -> dict:
    """
    Score the draft review on four criteria (0–10).
    Determine weakest criterion and verdict.
    """
    draft_review = state["draft_review"]
    prompt = f"""
You are a senior software engineer reviewing the following draft review.

Draft Review:
{draft_review}

Score this draft on four criteria (0-10, 10 being best):
1. PEP8 compliance
2. Type hints presence and correctness
3. Edge case handling
4. Naming conventions

Return a JSON object with keys:
- "criteria_scores": dict mapping criterion name to score
- "weakest_criterion": the criterion with lowest score
- "verdict": "ok" if all scores >=8, otherwise "needs_revision"

Example output:
{{
  "criteria_scores": {{
    "PEP8 compliance": 5,
    "Type hints presence and correctness": 3,
    "Edge case handling": 4,
    "Naming conventions": 5
  }},
  "weakest_criterion": "Type hints presence and correctness",
  "verdict": "needs_revision"
}}
"""
    response = llm.invoke(prompt)
    try:
        data = json.loads(response.content.strip())
    except Exception as e:
        raise ValueError(f"Failed to parse LLM JSON: {e}")
    return {
        "criteria_scores": data["criteria_scores"],
        "weakest_criterion": data["weakest_criterion"],
        "verdict": data["verdict"]
    }

def register(graph: StateGraph):
    graph.add_node("critic", critic)


from langgraph import StateGraph
from state import CodeReviewState
from langchain_openai import ChatOpenAI
import re

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

def rewrite(state: CodeReviewState) -> dict:
    """
    Rewrite only the section of draft_review corresponding to weakest_criterion.
    Increment round counter.
    """
    code = state["code"]
    draft_review = state["draft_review"]
    weakest = state["weakest_criterion"]

    # Find the line(s) that mention the weakest criterion
    pattern = re.compile(rf"(?i){re.escape(weakest)}.*?(?=\n\n|$)", re.DOTALL)
    match = pattern.search(draft_review)
    issue_section = match.group(0).strip() if match else ""

    prompt = f"""
You are a senior software engineer. The following Python function has an identified weak area:

```python
{code}
```

The draft review contains the following section about this weakness:
{issue_section}

Rewrite only that part of the review to improve it, keeping the rest of the draft unchanged. Return the updated full review as plain text.
"""
    response = llm.invoke(prompt)
    new_review = response.content.strip()

    # Replace old section with new one
    if match:
        updated_review = draft_review.replace(issue_section, new_review)
    else:
        updated_review = new_review

    return {
        "draft_review": updated_review,
        "round": state["round"] + 1
    }

def register(graph: StateGraph):
    graph.add_node("rewrite", rewrite)


from langgraph import StateGraph, END
from state import CodeReviewState
from nodes.draft_review_node import register as draft_register
from nodes.critic_node import register as critic_register
from nodes.rewrite_node import register as rewrite_register

def build_graph() -> StateGraph:
    """
    Build a LangGraph that performs:
    draft_review → critic → (optional) rewrite → critic … until verdict == 'ok' or max rounds reached.
    """
    workflow = StateGraph(CodeReviewState)

    # Register nodes
    draft_register(workflow)
    critic_register(workflow)
    rewrite_register(workflow)

    # Entry point
    workflow.set_entry_point("draft_review")

    # Conditional transition after critic
    def decide(state: CodeReviewState):
        if state["verdict"] == "ok":
            return END
        elif state["round"] < state.get("max_rounds", 2):
            return "rewrite"
        else:
            return END

    workflow.add_conditional_edges(
        ["critic"],
        decide,
        {
            "rewrite": "rewrite",
            END: END
        }
    )

    # After rewrite, go back to critic
    workflow.add_edge("rewrite", "critic")

    return workflow


import argparse
from graph import build_graph
from state import CodeReviewState
import os

def main():
    parser = argparse.ArgumentParser(description="LangGraph Code Review Agent")
    parser.add_argument("file", help="Path to a Python file containing the function to review")
    args = parser.parse_args()

    with open(args.file, "r") as f:
        code = f.read()

    # Initialize state
    state: CodeReviewState = {
        "code": code,
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": "",
        "verdict": "",
        "round": 1,
        "max_rounds": 2
    }

    graph = build_graph()
    final_state = graph.invoke(state)

    print("\n=== Draft Review ===")
    print(final_state["draft_review"])
    print("\n=== Criteria Scores ===")
    for crit, score in final_state.get("criteria_scores", {}).items():
        print(f"{crit}: {score}")
    print(f"\nWeakest Criterion: {final_state.get('weakest_criterion', '')}")
    print(f"Verdict: {final_state.get('verdict', '')}")

if __name__ == "__main__":
    main()
