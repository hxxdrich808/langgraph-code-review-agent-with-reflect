from typing import TypedDict, Dict

class CodeReviewState(TypedDict):
    code: str
    draft_review: str
    criteria_scores: Dict[str, int]  # {"pep8": 0-10, "type_hints": ..., "edge_cases": ..., "naming": ...}
    weakest_criterion: str
    verdict: str  # "ok" | "needs_revision"
    round: int
    max_rounds: int
