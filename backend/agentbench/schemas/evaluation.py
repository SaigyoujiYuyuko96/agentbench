from datetime import datetime
from pydantic import BaseModel

class EvaluationResultResponse(BaseModel):
    id: int
    test_run_id: int
    judge_type: str
    overall_score: float
    accuracy_score: float | None
    hallucination_score: float | None
    tool_correctness_score: float | None
    expression_quality_score: float | None
    judge_reasoning: str
    rule_results: list | None
    created_at: datetime
    model_config = {"from_attributes": True}
