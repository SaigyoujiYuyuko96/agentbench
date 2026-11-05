import inspect
import functools
from agentbench.runners.base import AgentRunner, RunResult

class PythonFnRunner(AgentRunner):
    """直接调用 Python async 函数。通过 @trace_step 装饰器收集 trace。"""

    async def run(self, test_input: str) -> RunResult:
        from agentbench.utils.trace_collector import TraceCollector
        collector = TraceCollector()

        fn = self.config.get("function")
        if fn is None:
            return RunResult(output="", collector=collector, error="No function provided in config")

        try:
            sig = inspect.signature(fn)
            if "step_collector" in sig.parameters:
                output = await fn(test_input, step_collector=collector)
            else:
                output = await fn(test_input)

            if not collector.get_steps():
                collector.record_step(
                    step_type="function_call", name=fn.__name__,
                    input_data={"input": test_input},
                    output_data={"output": output},
                )

            return RunResult(output=str(output) if output else "", collector=collector)

        except Exception as e:
            collector.record_step(
                step_type="function_call", name=fn.__name__,
                input_data={"input": test_input},
                status="error", error_message=str(e),
            )
            return RunResult(output="", collector=collector, error=str(e))


def trace_step(*, step_type: str, name: str = ""):
    """装饰器：将被装饰函数的执行记录为一个 trace 步骤。"""
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            collector = kwargs.get("step_collector")
            if collector and hasattr(collector, "record_step"):
                with collector.step(step_type=step_type, name=name or fn.__name__):
                    return await fn(*args, **{k: v for k, v in kwargs.items() if k != "step_collector"})
            return await fn(*args, **kwargs)
        return wrapper
    return decorator
