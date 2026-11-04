import pytest
from app.schemas.agent_config import AgentConfigCreate, AgentConfigUpdate
from app.services.agent_config_service import AgentConfigService

class TestAgentConfigService:
    @pytest.mark.asyncio
    async def test_create_agent_config(self, db_session):
        service = AgentConfigService(db_session)
        data = AgentConfigCreate(
            name="animepilot-v1",
            agent_type="openai_compatible",
            config={"endpoint": "http://localhost:8001/chat", "model": "gpt-4.1"},
        )
        ac = await service.create(data)
        assert ac.id is not None
        assert ac.name == "animepilot-v1"
        assert ac.agent_type == "openai_compatible"

    @pytest.mark.asyncio
    async def test_list_agent_configs(self, db_session):
        service = AgentConfigService(db_session)
        for t in ["langgraph", "http", "openai_compatible"]:
            await service.create(AgentConfigCreate(
                name=f"config-{t}", agent_type=t, config={},
            ))
        items, total = await service.list_()
        assert total == 3

    @pytest.mark.asyncio
    async def test_update_agent_config(self, db_session):
        service = AgentConfigService(db_session)
        created = await service.create(AgentConfigCreate(
            name="v1", agent_type="http", config={"endpoint": "http://old"},
        ))
        updated = await service.update(created.id, AgentConfigUpdate(
            config={"endpoint": "http://new"},
        ))
        assert "http://new" in updated.config

    @pytest.mark.asyncio
    async def test_delete_agent_config(self, db_session):
        service = AgentConfigService(db_session)
        created = await service.create(AgentConfigCreate(
            name="del", agent_type="http", config={},
        ))
        await service.delete(created.id)
        assert await service.get_by_id(created.id) is None
