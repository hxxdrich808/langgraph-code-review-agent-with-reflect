from langgraph import StateGraph
from state import CodeReviewState
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

def draft_review(state: CodeReviewState) -> dict:
    """
    Generate an initial review consisting of 3–6 concise points.
    """
    code = state["code"]
    prompt = f"""
You are a senior software engineer reviewing the following Python function.

```python
{code}
```

Provide an initial review with 3 to 6 concise bullet points. Do not include any JSON or formatting, just plain text.
"""
    response = llm.invoke(prompt)
    return {"draft_review": response.content.strip(), "round": 1}

def register(graph: StateGraph):
    graph.add_node("draft_review", draft_review)
