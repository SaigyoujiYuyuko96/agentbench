import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from agentbench.database import get_session
from agentbench.schemas.agent_config import (
    AgentConfigCreate, AgentConfigUpdate, AgentConfigResponse,
)
from agentbench.services.agent_config_service import AgentConfigService

router = APIRouter(prefix="/api/agent-configs", tags=["agent-configs"])

def _to_response(ac) -> AgentConfigResponse:
    return AgentConfigResponse(
        id=ac.id,
        name=ac.name,
        agent_type=ac.agent_type,
        config=json.loads(ac.config) if ac.config else {},
        description=ac.description,
        created_at=ac.created_at,
        updated_at=ac.updated_at,
    )

@router.post("/", response_model=AgentConfigResponse, status_code=201)
async def create_agent_config(
    data: AgentConfigCreate,
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    ac = await service.create(data)
    return _to_response(ac)

@router.get("/", response_model=dict)
async def list_agent_configs(
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    items, total = await service.list_()
    return {"items": [_to_response(ac) for ac in items], "total": total}

@router.get("/{agent_config_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    agent_config_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    ac = await service.get_by_id(agent_config_id)
    if ac is None:
        raise HTTPException(status_code=404, detail="AgentConfig not found")
    return _to_response(ac)

@router.put("/{agent_config_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    agent_config_id: int,
    data: AgentConfigUpdate,
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    ac = await service.update(agent_config_id, data)
    if ac is None:
        raise HTTPException(status_code=404, detail="AgentConfig not found")
    return _to_response(ac)

@router.delete("/{agent_config_id}", status_code=204)
async def delete_agent_config(
    agent_config_id: int,
    session: AsyncSession = Depends(get_session),
):
    service = AgentConfigService(session)
    deleted = await service.delete(agent_config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="AgentConfig not found")
