import json
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from agentbench.models.agent_config import AgentConfig
from agentbench.schemas.agent_config import AgentConfigCreate, AgentConfigUpdate

class AgentConfigService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: AgentConfigCreate) -> AgentConfig:
        ac = AgentConfig(
            name=data.name,
            agent_type=data.agent_type,
            config=json.dumps(data.config, ensure_ascii=False),
            description=data.description,
        )
        self.session.add(ac)
        await self.session.commit()
        await self.session.refresh(ac)
        return ac

    async def list_(self, *, skip: int = 0, limit: int = 50) -> tuple[list[AgentConfig], int]:
        count_query = select(func.count(AgentConfig.id))
        total = (await self.session.execute(count_query)).scalar() or 0
        query = select(AgentConfig).order_by(AgentConfig.created_at.desc()).offset(skip).limit(limit)
        items = list((await self.session.execute(query)).scalars().all())
        return items, total

    async def get_by_id(self, agent_config_id: int) -> AgentConfig | None:
        result = await self.session.execute(
            select(AgentConfig).where(AgentConfig.id == agent_config_id)
        )
        return result.scalar_one_or_none()

    async def update(self, agent_config_id: int, data: AgentConfigUpdate) -> AgentConfig | None:
        ac = await self.get_by_id(agent_config_id)
        if ac is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "config" in update_data and update_data["config"] is not None:
            update_data["config"] = json.dumps(update_data["config"], ensure_ascii=False)
        for key, value in update_data.items():
            setattr(ac, key, value)
        await self.session.commit()
        await self.session.refresh(ac)
        return ac

    async def delete(self, agent_config_id: int) -> bool:
        result = await self.session.execute(
            delete(AgentConfig).where(AgentConfig.id == agent_config_id)
        )
        await self.session.commit()
        return result.rowcount > 0
