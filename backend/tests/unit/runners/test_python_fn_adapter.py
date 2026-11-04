import pytest
from app.runners.python_fn_adapter import PythonFnRunner, trace_step

class TestPythonFnRunner:
    @pytest.mark.asyncio
    async def test_run_simple_function(self):
        async def my_agent(query: str) -> str:
            return f"收到：{query}"

        runner = PythonFnRunner({"function": my_agent})
        result = await runner.run("测试输入")
        assert result.output == "收到：测试输入"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_run_function_with_trace_decorator(self):
        @trace_step(step_type="intent_detection", name="MyDetector")
        async def detect_intent(query: str) -> str:
            return "search"

        async def my_agent(query: str, step_collector) -> str:
            intent = await detect_intent(query, step_collector=step_collector)
            return f"意图：{intent}"

        runner = PythonFnRunner({"function": my_agent})
        result = await runner.run("搜索动漫")
        assert "search" in result.output or "意图" in result.output

    @pytest.mark.asyncio
    async def test_run_function_raises_error(self):
        async def broken_agent(query: str) -> str:
            raise ValueError("测试错误")

        runner = PythonFnRunner({"function": broken_agent})
        result = await runner.run("测试")
        assert result.error is not None
        assert "测试错误" in result.error

    @pytest.mark.asyncio
    async def test_run_no_function_provided(self):
        runner = PythonFnRunner({})
        result = await runner.run("测试")
        assert result.error is not None
        assert "No function" in result.error
