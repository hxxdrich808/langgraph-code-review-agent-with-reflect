#!/usr/bin/env python3
"""
LangGraph Code Review Agent with Reflection

This script implements a LangGraph that:
1. Generates an initial draft review of a Python function.
2. Critiques the draft using four criteria (PEP8, type hints, edge cases, naming).
3. If any criterion is below 7, rewrites the review to strengthen the weakest point.
4. Repeats up to `max_rounds` times.

The output is displayed with Rich for readability.
"""

import os
from typing import TypedDict, Dict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from dotenv import load_dotenv

# Load environment variables (e.g., OPENAI_API_KEY)
load_dotenv()

console = Console()


class CodeReviewState(TypedDict):
    code: str
    draft_review: str
    criteria_scores: Dict[str, int]  # {"pep8": 0-10, ...}
    weakest_criterion: str | None
    verdict: str  # "ok" | "needs_revision"
    round: int
    max_rounds: int


# LLM configuration
llm = ChatOpenAI(
    temperature=0.2,
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
)

# ---------- Node definitions ----------
def draft_review_node(state: CodeReviewState) -> Dict:
    """Generate an initial review of the code."""
    prompt = f"""
You are a senior Python developer. Review the following function and provide 3–6 concise bullet points highlighting strengths and areas for improvement.

Function:
```python
{state["code"]}
```

Return only the review text.
"""
    response = llm.invoke(prompt)
    state["draft_review"] = response.content.strip()
    return {"draft_review": state["draft_review"]}


def reflect_node(state: CodeReviewState) -> Dict:
    """Critique the draft review on four criteria."""
    prompt = f"""
You are a code quality critic. Evaluate the following draft review on these four criteria:

- PEP8 compliance
- Type hints usage
- Edge case handling
- Naming conventions

For each criterion, assign an integer score from 0 to 10 (10 being perfect). Identify the weakest criterion and set verdict:
- "ok" if all scores are >=7
- "needs_revision" otherwise.

Return a JSON object with keys: pep8, type_hints, edge_cases, naming, weakest_criterion, verdict.

Draft review:
{state["draft_review"]}

JSON output only.
"""
    response = llm.invoke(prompt)
    import json

    scores = json.loads(response.content.strip())
    state["criteria_scores"] = {
        "pep8": int(scores["pep8"]),
        "type_hints": int(scores["type_hints"]),
        "edge_cases": int(scores["edge_cases"]),
        "naming": int(scores["naming"]),
    }
    state["weakest_criterion"] = scores["weakest_criterion"]
    state["verdict"] = scores["verdict"]
    return {
        "criteria_scores": state["criteria_scores"],
        "weakest_criterion": state["weakest_criterion"],
        "verdict": state["verdict"],
    }


def rewrite_node(state: CodeReviewState) -> Dict:
    """Rewrite the review to strengthen the weakest criterion."""
    prompt = f"""
You are a senior Python developer. The draft review below received low scores on the following criterion: {state['weakest_criterion']}. Rewrite the review to address this weakness, improving clarity and detail.

Original draft review:
{state['draft_review']}

Provide the revised review text only.
"""
    response = llm.invoke(prompt)
    state["draft_review"] = response.content.strip()
    return {"draft_review": state["draft_review"]}


# ---------- Graph construction ----------
def build_graph() -> StateGraph[CodeReviewState]:
    graph = StateGraph(CodeReviewState)

    # Add nodes
    graph.add_node("draft", draft_review_node)
    graph.add_node("reflect", reflect_node)
    graph.add_node("rewrite", rewrite_node)

    # Define transitions
    graph.set_entry_point("draft")
    graph.add_conditional_edges(
        "draft",
        lambda x: "reflect",
    )
    graph.add_conditional_edges(
        "reflect",
        lambda x: (
            "rewrite"
            if x["verdict"] == "needs_revision" and x["round"] < x["max_rounds"]
            else END
        ),
    )
    graph.add_edge("rewrite", "reflect")

    return graph


# ---------- Rich output helpers ----------
def display_initial(state: CodeReviewState):
    console.print(
        Panel(
            Markdown(f"### Original Function\n```python\n{state['code']}\n```"),
            title="Original Code",
        )
    )


def display_draft(state: CodeReviewState, round_num: int):
    console.print(
        Panel(
            Markdown(f"**Round {round_num} Draft Review**\n{state['draft_review']}"),
            title=f"Draft Review (Round {round_num})",
        )
    )


def display_scores(state: CodeReviewState):
    table = Table(title="Reflection Scores")
    table.add_column("Criterion", style="cyan")
    table.add_column("Score", justify="right")
    for crit, score in state["criteria_scores"].items():
        style = "bold red" if crit == state["weakest_criterion"] else ""
        table.add_row(crit.replace("_", " ").title(), str(score), style=style)
    console.print(table)


def display_final(state: CodeReviewState):
    verdict = state["verdict"]
    title = (
        f"[green]Final Verdict: {verdict.upper()}[/green]"
        if verdict == "ok"
        else f"[red]Final Verdict: {verdict.upper()}[/red]"
    )
    console.print(Panel(Markdown(f"{state['draft_review']}"), title=title))


# ---------- Demo function ----------
def demo_function() -> str:
    return """
def sort_numbers(arr):
    \"\"\"Return a sorted list of numbers.\"\"\"
    return sorted(arr)
"""


# ---------- CLI entry point ----------
def main():
    # Prepare initial state
    code_snippet = demo_function()
    max_rounds_env = os.getenv("MAX_ROUNDS")
    try:
        max_rounds = int(max_rounds_env) if max_rounds_env else 2
    except ValueError:
        max_rounds = 2

    init_state: CodeReviewState = {
        "code": code_snippet.strip(),
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": None,
        "verdict": "",
        "round": 1,
        "max_rounds": max_rounds,
    }

    graph_builder = build_graph()
    app = graph_builder.compile()

    # Run the graph
    state = init_state
    while True:
        console.print("\n[bold underline]Starting new round[/bold underline]\n")
        display_initial(state)
        result = app.invoke(state)

        # Update state with results
        for k, v in result.items():
            state[k] = v

        if "draft_review" in result:
            display_draft(state, state["round"])
        if "criteria_scores" in result:
            display_scores(state)

        if state["verdict"] == "ok":
            display_final(state)
            break
        elif state["round"] >= state["max_rounds"]:
            console.print("[red]Reached maximum rounds. Ending review.[/red]")
            display_final(state)
            break
        else:
            state["round"] += 1


if __name__ == "__main__":
    main()
