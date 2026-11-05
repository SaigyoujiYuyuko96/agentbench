import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agentbench.database import get_session
from agentbench.models.test_run import TestRun
from agentbench.models.run_step import RunStep
from agentbench.schemas.test_run import TestRunResponse
from agentbench.schemas.run_step import RunStepResponse
from agentbench.services.runner_service import RunnerService

router = APIRouter(prefix="/api/test-runs", tags=["test-runs"])

def _run_to_response(tr: TestRun) -> TestRunResponse:
    return TestRunResponse(
        id=tr.id,
        test_case_id=tr.test_case_id,
        agent_config_id=tr.agent_config_id,
        status=tr.status,
        agent_output=tr.agent_output,
        duration_ms=tr.duration_ms,
        total_tokens=tr.total_tokens,
        cost_estimate=tr.cost_estimate,
        error_message=tr.error_message,
        created_at=tr.created_at,
    )

def _step_to_response(rs: RunStep) -> RunStepResponse:
    return RunStepResponse(
        id=rs.id,
        test_run_id=rs.test_run_id,
        sequence=rs.sequence,
        step_type=rs.step_type,
        name=rs.name,
        input_json=json.loads(rs.input_json) if rs.input_json else {},
        output_json=json.loads(rs.output_json) if rs.output_json else {},
        latency_ms=rs.latency_ms,
        token_usage_input=rs.token_usage_input,
        token_usage_output=rs.token_usage_output,
        status=rs.status,
        error_message=rs.error_message,
    )

@router.post("/")
async def run_test(
    test_case_id: int,
    agent_config_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = RunnerService(session)
    try:
        test_run = await service.run_single(test_case_id, agent_config_id)
        return _run_to_response(test_run)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=list[TestRunResponse])
async def list_test_runs(
    test_case_id: int | None = None,
    agent_config_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    query = select(TestRun)
    if test_case_id:
        query = query.where(TestRun.test_case_id == test_case_id)
    if agent_config_id:
        query = query.where(TestRun.agent_config_id == agent_config_id)
    query = query.order_by(TestRun.id.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    return [_run_to_response(tr) for tr in result.scalars().all()]

@router.get("/{test_run_id}", response_model=TestRunResponse)
async def get_test_run(
    test_run_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(TestRun).where(TestRun.id == test_run_id))
    tr = result.scalar_one_or_none()
    if tr is None:
        raise HTTPException(status_code=404, detail="TestRun not found")
    return _run_to_response(tr)

@router.get("/{test_run_id}/steps", response_model=list[RunStepResponse])
async def get_run_steps(
    test_run_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(RunStep).where(RunStep.test_run_id == test_run_id).order_by(RunStep.sequence)
    )
    return [_step_to_response(rs) for rs in result.scalars().all()]
