import re
from dataclasses import dataclass
from app.evaluators.base import BaseEvaluator, EvaluationResult

@dataclass
class RuleSpec:
    type: str  # keyword_contains / keyword_not_contains / regex_match
    value: str

class RuleEvaluator(BaseEvaluator):
    def __init__(self, rules: list[RuleSpec]):
        self.rules = rules

    def evaluate(
        self,
        *,
        agent_output: str,
        expected: str = "",
        scoring_criteria: str = "",
        run_steps: list[dict] | None = None,
    ) -> EvaluationResult:
        if not self.rules:
            return EvaluationResult(
                judge_type="rule",
                overall_score=3.0,
                passed=True,
                reasoning="No rules defined, returning neutral score.",
                details={"total_count": 0, "passed_count": 0, "results": []},
            )

        passed_count = 0
        rule_results = []

        for rule in self.rules:
            matched = self._check_rule(rule, agent_output)
            rule_results.append({"rule_type": rule.type, "rule_value": rule.value, "matched": matched})
            if matched:
                passed_count += 1

        all_passed = passed_count == len(self.rules)
        score = 5.0 if all_passed else max(1.0, round(5.0 * passed_count / len(self.rules), 1))

        return EvaluationResult(
            judge_type="rule",
            overall_score=score,
            passed=all_passed,
            reasoning=f"{passed_count}/{len(self.rules)} rules passed.",
            details={"total_count": len(self.rules), "passed_count": passed_count, "results": rule_results},
        )

    def _check_rule(self, rule: RuleSpec, text: str) -> bool:
        if rule.type == "keyword_contains":
            return rule.value in text
        elif rule.type == "keyword_not_contains":
            return rule.value not in text
        elif rule.type == "regex_match":
            return bool(re.search(rule.value, text))
        return False
