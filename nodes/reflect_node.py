import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))

def reflect(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Critique the draft review and produce structured JSON with scores.
    """
    prompt = f"""You are a code quality critic. Evaluate the following code review:

{state["draft_review"]}

Score each of the four criteria on a scale 0-10:
- PEP8 compliance
- Type hints presence and correctness
- Edge case handling
- Naming conventions

Return a JSON object with keys:
"criteria_scores": {{"PEP8 compliance": int, "Type hints presence and correctness": int,
"Edge case handling": int, "Naming conventions": int}},
"weakest_criterion": string (the criterion name with the lowest score),
"verdict": "ok" if all scores >= 7 else "needs_revision"."""
    response = llm.invoke(prompt)
    try:
        data = json.loads(response.content.strip())
    except Exception as e:
        raise ValueError(f"Invalid JSON from LLM: {response.content}") from e

    # Validate keys
    required_keys = {"criteria_scores", "weakest_criterion", "verdict"}
    if not required_keys.issubset(data):
        raise ValueError("Missing keys in reflect output")

    state["criteria_scores"] = data["criteria_scores"]
    state["weakest_criterion"] = data["weakest_criterion"]
    state["verdict"] = data["verdict"]
    return state
