import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from agentbench.database import get_session
from agentbench.schemas.test_case import (
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
)
from agentbench.services.test_case_service import TestCaseService

router = APIRouter(prefix="/api/test-cases", tags=["test-cases"])

def _to_response(tc) -> TestCaseResponse:
    return TestCaseResponse(
        id=tc.id,
        title=tc.title,
        input_text=tc.input_text,
        expected_behavior=tc.expected_behavior,
        scoring_criteria=tc.scoring_criteria,
        tags=json.loads(tc.tags) if tc.tags else [],
        difficulty=tc.difficulty,
        category=tc.category,
        created_at=tc.created_at,
        updated_at=tc.updated_at,
    )

@router.post("/", response_model=TestCaseResponse, status_code=201)
async def create_test_case(
    data: TestCaseCreate,
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    tc = await service.create(data)
    return _to_response(tc)

@router.get("/", response_model=dict)
async def list_test_cases(
    difficulty: str | None = Query(None),
    category: str | None = Query(None),
    tag: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    items, total = await service.list_(
        difficulty=difficulty, category=category, tag=tag,
        skip=skip, limit=limit,
    )
    return {"items": [_to_response(tc) for tc in items], "total": total}

@router.get("/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(
    test_case_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    tc = await service.get_by_id(test_case_id)
    if tc is None:
        raise HTTPException(status_code=404, detail="TestCase not found")
    return _to_response(tc)

@router.put("/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(
    test_case_id: int,
    data: TestCaseUpdate,
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    tc = await service.update(test_case_id, data)
    if tc is None:
        raise HTTPException(status_code=404, detail="TestCase not found")
    return _to_response(tc)

@router.delete("/{test_case_id}", status_code=204)
async def delete_test_case(
    test_case_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = TestCaseService(session)
    deleted = await service.delete(test_case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="TestCase not found")
