import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))

def rewrite(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rewrite the section of the draft review that corresponds to the weakest criterion.
    """
    # Identify the line(s) in the draft_review that mention the weakest criterion
    weak = state["weakest_criterion"]
    lines = state["draft_review"].splitlines()
    new_lines = []
    for line in lines:
        if weak.lower() in line.lower():
            # Ask LLM to rewrite this line
            prompt = f"""Rewrite the following review point to better address the criterion:

{line}

Focus on improving {weak}. Return only the rewritten sentence."""
            response = llm.invoke(prompt)
            new_line = response.content.strip()
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    state["draft_review"] = "\n".join(new_lines).strip()
    # Increment round
    state["round"] += 1
    return state
