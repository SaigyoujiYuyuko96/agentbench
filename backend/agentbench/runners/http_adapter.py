import httpx
from agentbench.runners.base import AgentRunner, RunResult

class HTTPRunner(AgentRunner):
    """通过 HTTP 端点调用自定义 Agent。

    配置项：
    - endpoint: 请求 URL
    - method: HTTP 方法（默认 POST）
    - headers: 请求头（可用于鉴权）
    - timeout: 超时时间（秒，默认 60）
    - request_body_template: 请求体模板，用 {input} 占位用户输入（默认 {"input": "{input}"}）
    - output_field: 输出字段路径，用点号分隔（如 "answer"、"data.output"，默认 "output"）
    - trace_field: trace 数组字段路径（默认 "trace"）
    """

    async def run(self, test_input: str) -> RunResult:
        from agentbench.utils.trace_collector import TraceCollector
        collector = TraceCollector()

        endpoint = self.config.get("endpoint", "")
        method = self.config.get("method", "POST").upper()
        headers = self.config.get("headers", {})
        timeout = self.config.get("timeout", 60)
        request_template = self.config.get("request_body_template", {"input": "{input}"})
        output_field = self.config.get("output_field", "output")
        trace_field = self.config.get("trace_field", "trace")

        def _build_payload(template, value):
            if isinstance(template, dict):
                return {k: _build_payload(v, value) for k, v in template.items()}
            if isinstance(template, str) and "{input}" in template:
                return template.replace("{input}", value)
            return template

        payload = _build_payload(request_template, test_input)

        def _get_nested(data, path):
            keys = path.split(".")
            current = data
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                else:
                    return None
            return current

        try:
            with collector.step(step_type="http_call", name=f"HTTP {method}", input_data=payload):
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.request(method, endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

            output = _get_nested(data, output_field) or ""

            trace_data = _get_nested(data, trace_field) or []
            for t in trace_data:
                collector.record_step(
                    step_type=t.get("step_type", "unknown"),
                    name=t.get("name", ""),
                    input_data=t.get("input"),
                    output_data=t.get("output"),
                    latency_ms=t.get("latency_ms", 0),
                    token_input=t.get("token_input", 0),
                    token_output=t.get("token_output", 0),
                    status=t.get("status", "success"),
                    error_message=t.get("error_message"),
                )

            return RunResult(output=output, collector=collector)

        except Exception as e:
            collector.record_step(
                step_type="http_call", name=f"HTTP {method}",
                input_data=payload, status="error", error_message=str(e),
            )
            return RunResult(output="", collector=collector, error=str(e))
