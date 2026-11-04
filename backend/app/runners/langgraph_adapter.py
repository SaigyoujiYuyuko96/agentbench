from app.runners.base import AgentRunner, RunResult

class LangGraphRunner(AgentRunner):
    """执行编译后的 LangGraph workflow。config 中需传入 'graph' 键对应的编译图。"""

    async def run(self, test_input: str) -> RunResult:
        from app.utils.trace_collector import TraceCollector
        collector = TraceCollector()

        graph = self.config.get("graph")
        if graph is None:
            return RunResult(output="", collector=collector, error="No 'graph' in config")

        state_input = {"messages": [{"role": "user", "content": test_input}]}

        try:
            with collector.step(step_type="graph_execution", name="LangGraph", input_data=state_input):
                result_state = await graph.ainvoke(state_input)

            messages = result_state.get("messages", [])
            output = ""
            for msg in messages:
                if hasattr(msg, "content") and hasattr(msg, "type") and msg.type == "ai":
                    output += msg.content
                elif isinstance(msg, dict) and msg.get("role") == "assistant":
                    output += msg.get("content", "")

            return RunResult(output=output, collector=collector)

        except Exception as e:
            collector.record_step(
                step_type="graph_execution", name="LangGraph",
                input_data=state_input, status="error", error_message=str(e),
            )
            return RunResult(output="", collector=collector, error=str(e))
