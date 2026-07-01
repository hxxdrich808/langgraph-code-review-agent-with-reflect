# LangGraph Code Review Agent with Reflection

## Requirements
- [high] Define State: Create a TypedDict `CodeReviewState` with fields: code (str), draft_review (str), criteria_scores (dict[str,int]), weakest_criterion (str), verdict ('ok'|'needs_revision'), round (int), max_rounds (int, default 2).
- [high] Draft Review Node: Implement a LangGraph node that takes `code` and produces a draft review containing 3–6 bullet points. The output should be plain text.
- [high] Reflect Node: Create an LLM-powered node that receives the draft review and assigns integer scores (0–10) for each of the four criteria, determines the weakest criterion, and sets the verdict ('ok' if all scores >= 7 else 'needs_revision'). The output must be structured so that the state can be updated with `criteria_scores`, `weakest_criterion`, and `verdict`.
- [normal] Rewrite Node: Implement a node that rewrites only the section of the draft review corresponding to the weakest criterion, incrementing `round` by 1. The rewritten text should improve on the identified weakness.
- [high] Graph Flow: Configure the LangGraph flow: START → draft_review → reflect. If verdict is 'ok', transition to END. If 'needs_revision' and round < max_rounds, go to rewrite → reflect; otherwise END.
- [normal] CLI Demo: Provide a command-line interface that accepts a Python function (e.g., `def sort_numbers(arr): return sorted(arr)`), runs the graph, and prints: initial draft review, scores with weakest criterion, any rewritten sections, and final verdict. Include a README explaining usage.
- [low] Testing: Write unit tests for state transitions, score calculations, and rewrite logic to ensure correct behavior across rounds.
