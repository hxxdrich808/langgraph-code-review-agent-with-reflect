# LangGraph Code Review Agent with Reflection

## Requirements
- [high] State Definition: Create CodeReviewState TypedDict with fields: code (str), draft_review (str), criteria_scores (dict[str,int]), weakest_criterion (str), verdict ("ok"|"needs_revision"), round (int), max_rounds (int).
- [high] Draft Review Node: Implement a node that generates 3–6 bullet points of code review for the provided function.
- [high] Reflect Node: Implement an LLM critic node that outputs structured scores (0‑10) for each criterion, determines weakest_criterion and verdict. Scores should be stored in criteria_scores.
- [high] Rewrite Node: Implement a node that rewrites only the section of draft_review corresponding to weakest_criterion, increments round, and updates state accordingly.
- [high] Graph Flow: Configure LangGraph with transitions: START → draft_review → reflect. If verdict is "ok" end; if "needs_revision" and round < max_rounds go to rewrite → reflect; otherwise end.
- [normal] Default Max Rounds: Set default max_rounds to 2 unless overridden in state.
- [high] CLI Demo: Provide a command‑line demo using a sample function (e.g., sort_numbers). Show logs of draft review, scores, and any rewrites until termination.
- [normal] Documentation: Include README with setup instructions, usage examples, and explanation of the graph logic.
