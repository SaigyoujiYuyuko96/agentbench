import pytest
from unittest.mock import AsyncMock, patch
from agentbench.runners.openai_adapter import OpenAICompatibleRunner
from agentbench.runners.http_adapter import HTTPRunner
from agentbench.runners.python_fn_adapter import PythonFnRunner
from agentbench.models.test_case import TestCase
from agentbench.models.agent_config import AgentConfig
from agentbench.services.runner_service import RunnerService

class TestRunnerService:
    @pytest.mark.asyncio
    async def test_select_adapter_type(self, db_session):
        service = RunnerService(db_session)
        assert service._adapter_class("openai_compatible") == OpenAICompatibleRunner
        assert service._adapter_class("http") == HTTPRunner
        assert service._adapter_class("python_fn") == PythonFnRunner

    @pytest.mark.asyncio
    async def test_invalid_adapter_type_raises(self, db_session):
        service = RunnerService(db_session)
        with pytest.raises(ValueError, match="Unknown agent type"):
            service._adapter_class("nonexistent_type")

    @pytest.mark.asyncio
    async def test_run_single_test_case_not_found(self, db_session):
        service = RunnerService(db_session)
        with pytest.raises(ValueError, match="TestCase"):
            await service.run_single(999, 1)

    @pytest.mark.asyncio
    async def test_run_single_agent_config_not_found(self, db_session):
        tc = TestCase(title="t", input_text="hi", expected_behavior="hello", scoring_criteria="")
        db_session.add(tc)
        await db_session.commit()
        service = RunnerService(db_session)
        with pytest.raises(ValueError, match="AgentConfig"):
            await service.run_single(tc.id, 999)
