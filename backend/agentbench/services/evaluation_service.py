import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agentbench.models.test_case import TestCase
from agentbench.models.test_run import TestRun
from agentbench.models.run_step import RunStep
from agentbench.models.evaluation_result import EvaluationResult
from agentbench.evaluators.rule_evaluator import RuleEvaluator, RuleSpec
from agentbench.evaluators.llm_judge_evaluator import LLMJudgeEvaluator
from agentbench.config import settings


class EvaluationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def evaluate_test_run(
        self,
        test_run_id: int,
        *,
        rules: list[RuleSpec] | None = None,
        use_llm_judge: bool = False,
    ) -> EvaluationResult:
        tr = (await self.session.execute(select(TestRun).where(TestRun.id == test_run_id))).scalar_one_or_none()
        if tr is None:
            raise ValueError(f"TestRun {test_run_id} not found")

        tc = (await self.session.execute(select(TestCase).where(TestCase.id == tr.test_case_id))).scalar_one_or_none()
        if tc is None:
            raise ValueError(f"TestCase {tr.test_case_id} not found")

        steps_result = await self.session.execute(
            select(RunStep).where(RunStep.test_run_id == test_run_id).order_by(RunStep.sequence)
        )
        run_steps = [{"step_type": s.step_type, "name": s.name, "status": s.status, "latency_ms": s.latency_ms} for s in steps_result.scalars().all()]

        best_result = None

        if rules:
            rule_eval = RuleEvaluator(rules)
            rule_result = rule_eval.evaluate(
                agent_output=tr.agent_output,
                expected=tc.expected_behavior,
                scoring_criteria=tc.scoring_criteria,
                run_steps=run_steps,
            )
            best_result = rule_result

        if use_llm_judge:
            judge = LLMJudgeEvaluator(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                model=settings.llm_judge_model,
            )
            llm_result = await judge.evaluate_async(
                agent_output=tr.agent_output,
                expected=tc.expected_behavior,
                scoring_criteria=tc.scoring_criteria,
                run_steps=run_steps,
            )
            if best_result is None or llm_result.overall_score > best_result.overall_score:
                best_result = llm_result

        if best_result is None:
            from agentbench.evaluators.base import EvaluationResult as BaseResult
            best_result = BaseResult(
                judge_type="none", overall_score=0.0, passed=False,
                reasoning="No evaluation method specified.",
            )

        db_eval = EvaluationResult(
            test_run_id=test_run_id,
            judge_type=best_result.judge_type,
            overall_score=best_result.overall_score,
            accuracy_score=best_result.details.get("accuracy"),
            hallucination_score=best_result.details.get("hallucination"),
            tool_correctness_score=best_result.details.get("tool_correctness"),
            expression_quality_score=best_result.details.get("expression_quality"),
            judge_reasoning=best_result.reasoning,
            rule_results=json.dumps(best_result.details.get("results", []), ensure_ascii=False) if best_result.details.get("results") else None,
        )
        self.session.add(db_eval)
        await self.session.commit()
        await self.session.refresh(db_eval)
        return db_eval
