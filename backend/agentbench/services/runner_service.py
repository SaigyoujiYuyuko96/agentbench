import json
import time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agentbench.models.test_case import TestCase
from agentbench.models.agent_config import AgentConfig
from agentbench.models.test_run import TestRun
from agentbench.models.run_step import RunStep
from agentbench.runners.base import RunResult
from agentbench.runners.registry import ADAPTER_MAP

class RunnerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _adapter_class(self, agent_type: str):
        cls = ADAPTER_MAP.get(agent_type)
        if cls is None:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return cls

    async def run_single(self, test_case_id: int, agent_config_id: int) -> TestRun:
        tc = (await self.session.execute(select(TestCase).where(TestCase.id == test_case_id))).scalar_one_or_none()
        ac = (await self.session.execute(select(AgentConfig).where(AgentConfig.id == agent_config_id))).scalar_one_or_none()
        if tc is None:
            raise ValueError(f"TestCase {test_case_id} not found")
        if ac is None:
            raise ValueError(f"AgentConfig {agent_config_id} not found")

        test_run = TestRun(
            test_case_id=test_case_id,
            agent_config_id=agent_config_id,
            status="running",
        )
        self.session.add(test_run)
        await self.session.commit()
        await self.session.refresh(test_run)

        config_dict = json.loads(ac.config) if ac.config else {}
        adapter_cls = self._adapter_class(ac.agent_type)
        runner = adapter_cls(config_dict)

        start_time = time.monotonic()
        try:
            result: RunResult = await runner.run(tc.input_text)
            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            test_run.status = "error" if result.error else "success"
            test_run.agent_output = result.output
            test_run.duration_ms = elapsed_ms
            test_run.total_tokens = result.collector.total_tokens()
            test_run.error_message = result.error

            for step_dict in result.collector.to_run_step_dicts(test_run.id):
                self.session.add(RunStep(**step_dict))

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            test_run.status = "error"
            test_run.error_message = str(e)
            test_run.duration_ms = elapsed_ms

        await self.session.commit()
        await self.session.refresh(test_run)
        return test_run
