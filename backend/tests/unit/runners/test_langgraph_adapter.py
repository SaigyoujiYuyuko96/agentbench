import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.runners.langgraph_adapter import LangGraphRunner

class TestLangGraphRunner:
    @pytest.mark.asyncio
    async def test_run_compiled_graph(self):
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "messages": [{"role": "assistant", "content": "推荐 CLANNAD。"}],
        })

        runner = LangGraphRunner({"graph": mock_graph})
        result = await runner.run("推荐治愈系动漫")
        assert "CLANNAD" in result.output
        steps = result.collector.get_steps()
        assert len(steps) >= 1

    @pytest.mark.asyncio
    async def test_run_handles_graph_error(self):
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=Exception("Graph execution failed"))

        runner = LangGraphRunner({"graph": mock_graph})
        result = await runner.run("测试")
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_run_no_graph_provided(self):
        runner = LangGraphRunner({})
        result = await runner.run("测试")
        assert result.error is not None
        assert "graph" in result.error
