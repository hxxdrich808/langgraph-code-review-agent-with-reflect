from langgraph import StateGraph
from state import CodeReviewState
from langchain_openai import ChatOpenAI
import json

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

def reflect(state: CodeReviewState) -> dict:
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
    graph.add_node("reflect", reflect)
