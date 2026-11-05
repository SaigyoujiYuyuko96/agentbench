from dataclasses import dataclass, field

@dataclass
class EvaluationResult:
    judge_type: str
    overall_score: float
    passed: bool
    reasoning: str = ""
    details: dict = field(default_factory=dict)

class BaseEvaluator:
    """评测基类。子类实现 evaluate 方法。"""

    def evaluate(
        self,
        *,
        agent_output: str,
        expected: str,
        scoring_criteria: str,
        run_steps: list[dict] | None = None,
    ) -> EvaluationResult:
        raise NotImplementedError
