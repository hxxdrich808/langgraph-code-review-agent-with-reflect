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
