import os
from langchain_openai import ChatOpenAI
from typing import Dict, Any

# LLM instance used by tests for patching
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))

def draft_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an initial code review with 3–6 bullet points.
    """
    prompt = f"""You are a senior Python developer reviewing the following function.

```python
{state["code"]}
```

Provide 3-6 concise bullet points describing what is good and what could be improved. Return only the bullet list, no additional text."""
    response = llm.invoke(prompt)
    # The LLM returns a string; we store it directly.
    state["draft_review"] = response.content.strip()
    return state
