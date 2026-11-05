import re
from dataclasses import dataclass
from agentbench.evaluators.base import BaseEvaluator, EvaluationResult

# `RuleSpec.type` 允许取什么，这里说了算。命令行解析 suite 时 import 的是同一
# 组常量，不在别处再抄一份，免得加了新规则而 YAML 那侧还拒收。
KEYWORD_CONTAINS = "keyword_contains"
KEYWORD_NOT_CONTAINS = "keyword_not_contains"
REGEX_MATCH = "regex_match"

RULE_TYPES = frozenset({KEYWORD_CONTAINS, KEYWORD_NOT_CONTAINS, REGEX_MATCH})

# 规则名 → 判定函数。判定函数的第一个参数是规则值，第二个是被测文本。
# 用查表而不是 if/elif 级联：规则集合和分派逻辑就不会各改各的、慢慢对不上。
_RULE_CHECKS = {
    KEYWORD_CONTAINS: lambda value, text: value in text,
    KEYWORD_NOT_CONTAINS: lambda value, text: value not in text,
    REGEX_MATCH: lambda value, text: bool(re.search(value, text)),
}


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
        check = _RULE_CHECKS.get(rule.type)
        if check is None:
            return False
        return check(rule.value, text)
