import asyncio
import argparse
from typing import TypedDict, Dict, Any
from pathlib import Path

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

load_dotenv()  # Load OPENAI_API_KEY if present


class CodeReviewState(TypedDict):
    code: str
    draft_review: str
    criteria_scores: Dict[str, int]
    weakest_criterion: str
    verdict: str  # "ok" | "needs_revision"
    round: int
    max_rounds: int


# LLM instance (you can switch to Ollama or other providers)
llm = ChatOpenAI(temperature=0.2)


def draft_review(state: CodeReviewState) -> Dict[str, Any]:
    """Generate a draft code review with 3-6 points."""
    prompt = f"""
You are an experienced Python reviewer. Provide a concise code review for the following function.
The review should contain 3 to 6 bullet points highlighting strengths and areas for improvement.

Function:
{state["code"]}

Review:
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"draft_review": response.content.strip()}


def reflect(state: CodeReviewState) -> Dict[str, Any]:
    """Critic evaluates the draft review on four criteria and returns structured JSON."""
    prompt = f"""
You are a code quality critic. Evaluate the following draft review on these four criteria:
- PEP8 compliance
- Type hints usage
- Edge case handling
- Naming conventions

Assign each criterion a score from 0 to 10 (integer). Identify the weakest criterion and provide an overall verdict: "ok" if all scores are >=7, otherwise "needs_revision".

Return a JSON object with keys:
pep8, type_hints, edge_cases, naming, weakest_criterion, verdict

Draft review:
{state["draft_review"]}

JSON:
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        import json
        data = json.loads(response.content.strip())
        return {
            "criteria_scores": {
                "pep8": int(data.get("pep8", 0)),
                "type_hints": int(data.get("type_hints", 0)),
                "edge_cases": int(data.get("edge_cases", 0)),
                "naming": int(data.get("naming", 0)),
            },
            "weakest_criterion": data.get("weakest_criterion", ""),
            "verdict": data.get("verdict", "needs_revision"),
        }
    except Exception as e:
        # Fallback in case of parsing error
        return {
            "criteria_scores": {"pep8": 0, "type_hints": 0, "edge_cases": 0, "naming": 0},
            "weakest_criterion": "",
            "verdict": "needs_revision",
        }


def rewrite(state: CodeReviewState) -> Dict[str, Any]:
    """Rewrite the draft review focusing on the weakest criterion."""
    prompt = f"""
You are a senior Python reviewer. The previous draft review was:
{state["draft_review"]}

The critic identified '{state['weakest_criterion']}' as the weakest area.
Improve the review by adding more detailed feedback specifically targeting this weakness.
Keep the overall structure (bullet points) and ensure clarity.

Revised Review:
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"draft_review": response.content.strip()}


def build_graph() -> StateGraph[CodeReviewState]:
    graph = StateGraph(CodeReviewState)

    # Add nodes
    graph.add_node("draft_review", draft_review)
    graph.add_node("reflect", reflect)
    graph.add_node("rewrite", rewrite)

    # Define transitions
    def to_reflect(state: CodeReviewState):
        return "reflect"

    def decide_next(state: CodeReviewState):
        if state["verdict"] == "ok":
            return END
        if state["round"] >= state["max_rounds"]:
            return END
        return "rewrite"

    graph.set_entry_point("draft_review")
    graph.add_edge("draft_review", to_reflect)
    graph.add_edge("reflect", decide_next)
    graph.add_edge("rewrite", "reflect")

    return graph


async def run_graph(code: str, max_rounds: int = 2) -> CodeReviewState:
    """Execute the LangGraph workflow and return final state."""
    graph = build_graph()
    initial_state: CodeReviewState = {
        "code": code,
        "draft_review": "",
        "criteria_scores": {},
        "weakest_criterion": "",
        "verdict": "",
        "round": 1,
        "max_rounds": max_rounds,
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state


def display_results(state: CodeReviewState):
    console = Console()
    console.print("\n[bold underline]Final Review[/]\n")
    console.print(Panel(state["draft_review"], title="Draft Review", expand=False))

    table = Table(title="Criteria Scores")
    table.add_column("Criterion", style="cyan")
    table.add_column("Score", justify="right", style="magenta")

    for crit, score in state["criteria_scores"].items():
        table.add_row(crit.replace("_", " ").title(), str(score))

    console.print(table)

    console.print(f"\n[bold]Weakest Criterion:[/] {state['weakest_criterion']}")
    console.print(f"[bold]Verdict:[/] {state['verdict'].upper()}\n")


def main():
    parser = argparse.ArgumentParser(description="LangGraph Code Review Agent")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Path to a Python file containing the function.")
    group.add_argument("--code", type=str, help="Raw code string of the function.")
    parser.add_argument("--max-rounds", type=int, default=2, help="Maximum number of rewrite rounds.")
    args = parser.parse_args()

    if args.file:
        code = args.file.read_text()
    else:
        code = args.code

    final_state = asyncio.run(run_graph(code, max_rounds=args.max_rounds))
    display_results(final_state)


if __name__ == "__main__":
    main()
