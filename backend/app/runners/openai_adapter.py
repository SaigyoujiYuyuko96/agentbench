import httpx
from app.runners.base import AgentRunner, RunResult

class OpenAICompatibleRunner(AgentRunner):
    """通过 OpenAI 兼容 API 执行 LLM 调用。"""

    async def run(self, test_input: str) -> RunResult:
        from app.utils.trace_collector import TraceCollector
        collector = TraceCollector()
        endpoint = self.config.get("endpoint", "https://api.openai.com/v1/chat/completions")
        model = self.config.get("model", "gpt-4.1")
        api_key = self.config.get("api_key", "")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": test_input}],
        }

        try:
            with collector.step(step_type="llm_generation", name="OpenAI Chat", input_data=payload):
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

            choices = data.get("choices", [])
            output = choices[0]["message"]["content"] if choices else ""
            usage = data.get("usage", {})

            if collector.get_steps():
                collector.get_steps()[-1]["token_usage_input"] = usage.get("prompt_tokens", 0)
                collector.get_steps()[-1]["token_usage_output"] = usage.get("completion_tokens", 0)

            return RunResult(output=output, collector=collector)

        except Exception as e:
            collector.record_step(
                step_type="llm_generation", name="OpenAI Chat",
                input_data=payload, status="error", error_message=str(e),
            )
            return RunResult(output="", collector=collector, error=str(e))
