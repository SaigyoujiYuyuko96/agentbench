import pytest
from app.models.test_run import TestRun
from app.models.run_step import RunStep
from app.models.evaluation_result import EvaluationResult
from app.models.test_case import TestCase
from app.models.agent_config import AgentConfig

class TestTestRunModel:
    @pytest.mark.asyncio
    async def test_create_test_run(self, db_session):
        tr = TestRun(
            test_case_id=1,
            agent_config_id=1,
            status="pending",
        )
        db_session.add(tr)
        await db_session.commit()
        await db_session.refresh(tr)
        assert tr.id is not None
        assert tr.status == "pending"

class TestRunStepModel:
    @pytest.mark.asyncio
    async def test_create_run_step(self, db_session):
        step = RunStep(
            test_run_id=1,
            sequence=1,
            step_type="intent_detection",
            name="IntentDetector",
            input_json='{"query": "搜索动漫"}',
            output_json='{"intent": "search"}',
            latency_ms=150,
            status="success",
        )
        db_session.add(step)
        await db_session.commit()
        await db_session.refresh(step)
        assert step.id is not None
        assert step.latency_ms == 150

class TestEvaluationResultModel:
    @pytest.mark.asyncio
    async def test_create_evaluation(self, db_session):
        ev = EvaluationResult(
            test_run_id=1,
            judge_type="rule",
            overall_score=4.0,
            accuracy_score=4.0,
            hallucination_score=5.0,
            tool_correctness_score=4.0,
            expression_quality_score=3.0,
            judge_reasoning="回答准确，无明显幻觉",
        )
        db_session.add(ev)
        await db_session.commit()
        await db_session.refresh(ev)
        assert ev.id is not None
        assert ev.overall_score == 4.0
