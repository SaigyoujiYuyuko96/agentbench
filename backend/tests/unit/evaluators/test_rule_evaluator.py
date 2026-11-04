import pytest
from app.evaluators.rule_evaluator import RuleEvaluator, RuleSpec

class TestRuleEvaluator:
    def test_keyword_contains_pass(self):
        evaluator = RuleEvaluator([RuleSpec(type="keyword_contains", value="CLANNAD")])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是一部经典动画。",
            expected="返回 CLANNAD",
            scoring_criteria="必须提到 CLANNAD",
        )
        assert result.passed is True
        assert result.overall_score >= 4.0

    def test_keyword_contains_fail(self):
        evaluator = RuleEvaluator([RuleSpec(type="keyword_contains", value="CLANNAD")])
        result = evaluator.evaluate(
            agent_output="这是一部治愈系动画。",
            expected="返回 CLANNAD",
            scoring_criteria="必须提到 CLANNAD",
        )
        assert result.passed is False

    def test_keyword_not_contains_pass(self):
        evaluator = RuleEvaluator([RuleSpec(type="keyword_not_contains", value="不知道")])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是一部 2007 年的动画。",
            expected="不应说不知道",
            scoring_criteria="",
        )
        assert result.passed is True

    def test_regex_match(self):
        evaluator = RuleEvaluator([RuleSpec(type="regex_match", value=r"\d{4}年")])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是 2007年的动画。",
            expected="包含年份",
            scoring_criteria="",
        )
        assert result.passed is True

    def test_multiple_rules_all_pass(self):
        evaluator = RuleEvaluator([
            RuleSpec(type="keyword_contains", value="CLANNAD"),
            RuleSpec(type="keyword_not_contains", value="不知道"),
        ])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是经典动画。",
            expected="包含 CLANNAD",
            scoring_criteria="",
        )
        assert result.passed is True
        assert result.details["passed_count"] == 2
        assert result.details["total_count"] == 2

    def test_multiple_rules_partial_pass(self):
        evaluator = RuleEvaluator([
            RuleSpec(type="keyword_contains", value="CLANNAD"),
            RuleSpec(type="keyword_contains", value="2007"),
        ])
        result = evaluator.evaluate(
            agent_output="CLANNAD 是经典动画。",
            expected="",
            scoring_criteria="",
        )
        assert result.passed is False
        assert result.details["passed_count"] == 1

    def test_empty_rules_returns_neutral(self):
        evaluator = RuleEvaluator([])
        result = evaluator.evaluate(agent_output="anything", expected="", scoring_criteria="")
        assert result.passed is True
        assert result.overall_score == 3.0
