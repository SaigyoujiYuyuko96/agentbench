import pytest
from app.services.evaluation_service import EvaluationService
from app.evaluators.rule_evaluator import RuleSpec

class TestEvaluationService:
    @pytest.mark.asyncio
    async def test_evaluate_with_rules(self, db_session):
        from app.models.test_case import TestCase
        from app.models.agent_config import AgentConfig
        from app.models.test_run import TestRun

        tc = TestCase(title="t", input_text="hi", expected_behavior="hello", scoring_criteria="", tags="[]")
        ac = AgentConfig(name="ac", agent_type="http", config="{}")
        tr = TestRun(test_case_id=1, agent_config_id=1, status="success", agent_output="hello world")
        db_session.add_all([tc, ac, tr])
        await db_session.commit()

        service = EvaluationService(db_session)
        result = await service.evaluate_test_run(
            test_run_id=tr.id,
            rules=[RuleSpec(type="keyword_contains", value="hello")],
            use_llm_judge=False,
        )
        assert result is not None
        assert result.judge_type == "rule"
        assert result.overall_score == 5.0

    @pytest.mark.asyncio
    async def test_evaluate_without_rules_no_llm(self, db_session):
        from app.models.test_case import TestCase
        from app.models.agent_config import AgentConfig
        from app.models.test_run import TestRun

        tc = TestCase(title="t2", input_text="hi", expected_behavior="hello", scoring_criteria="", tags="[]")
        ac = AgentConfig(name="ac2", agent_type="http", config="{}")
        tr = TestRun(test_case_id=1, agent_config_id=1, status="success", agent_output="test")
        db_session.add_all([tc, ac, tr])
        await db_session.commit()

        service = EvaluationService(db_session)
        result = await service.evaluate_test_run(
            test_run_id=tr.id, rules=[], use_llm_judge=False,
        )
        assert result is not None
        assert result.judge_type == "none"

    @pytest.mark.asyncio
    async def test_evaluate_test_run_not_found(self, db_session):
        service = EvaluationService(db_session)
        with pytest.raises(ValueError, match="TestRun"):
            await service.evaluate_test_run(999, rules=[], use_llm_judge=False)
