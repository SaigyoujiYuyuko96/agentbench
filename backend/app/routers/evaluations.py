import json
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_session
from app.models.evaluation_result import EvaluationResult
from app.schemas.evaluation import EvaluationResultResponse
from app.services.evaluation_service import EvaluationService
from app.evaluators.rule_evaluator import RuleSpec

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


class EvaluateRequest(BaseModel):
    test_run_id: int
    rules: list[dict] | None = None
    use_llm_judge: bool = False


def _to_response(ev: EvaluationResult) -> EvaluationResultResponse:
    return EvaluationResultResponse(
        id=ev.id,
        test_run_id=ev.test_run_id,
        judge_type=ev.judge_type,
        overall_score=ev.overall_score,
        accuracy_score=ev.accuracy_score,
        hallucination_score=ev.hallucination_score,
        tool_correctness_score=ev.tool_correctness_score,
        expression_quality_score=ev.expression_quality_score,
        judge_reasoning=ev.judge_reasoning,
        rule_results=json.loads(ev.rule_results) if ev.rule_results else None,
        created_at=ev.created_at,
    )


@router.post("/")
async def evaluate_run(
    payload: EvaluateRequest,
    session: AsyncSession = Depends(get_session),
):
    rule_specs = [RuleSpec(**r) for r in payload.rules] if payload.rules else []
    service = EvaluationService(session)
    try:
        result = await service.evaluate_test_run(
            payload.test_run_id, rules=rule_specs, use_llm_judge=payload.use_llm_judge,
        )
        return _to_response(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{evaluation_id}", response_model=EvaluationResultResponse)
async def get_evaluation(
    evaluation_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(EvaluationResult).where(EvaluationResult.id == evaluation_id)
    )
    ev = result.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=404, detail="EvaluationResult not found")
    return _to_response(ev)

@router.get("/run/{test_run_id}", response_model=list[EvaluationResultResponse])
async def get_evaluations_by_run(
    test_run_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(EvaluationResult).where(EvaluationResult.test_run_id == test_run_id)
    )
    return [_to_response(ev) for ev in result.scalars().all()]
