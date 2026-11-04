import json
import time
from contextlib import contextmanager

class TraceCollector:
    def __init__(self):
        self._steps: list[dict] = []
        self._sequence = 0

    def record_step(
        self,
        *,
        step_type: str,
        name: str = "",
        input_data: dict | None = None,
        output_data: dict | None = None,
        latency_ms: int = 0,
        token_input: int = 0,
        token_output: int = 0,
        status: str = "success",
        error_message: str | None = None,
    ) -> None:
        self._sequence += 1
        self._steps.append({
            "sequence": self._sequence,
            "step_type": step_type,
            "name": name,
            "input_json": json.dumps(input_data or {}, ensure_ascii=False),
            "output_json": json.dumps(output_data or {}, ensure_ascii=False),
            "latency_ms": latency_ms,
            "token_usage_input": token_input,
            "token_usage_output": token_output,
            "status": status,
            "error_message": error_message,
        })

    @contextmanager
    def step(self, *, step_type: str, name: str = "", input_data: dict | None = None):
        start = time.monotonic()
        yield
        latency_ms = int((time.monotonic() - start) * 1000)
        self.record_step(
            step_type=step_type, name=name,
            input_data=input_data, latency_ms=latency_ms,
        )

    def get_steps(self) -> list[dict]:
        return list(self._steps)

    def to_run_step_dicts(self, test_run_id: int) -> list[dict]:
        result = []
        for s in self._steps:
            d = {"test_run_id": test_run_id}
            d.update(s)
            result.append(d)
        return result

    def total_tokens(self) -> int:
        return sum(s["token_usage_input"] + s["token_usage_output"] for s in self._steps)

    def total_latency_ms(self) -> int:
        return sum(s["latency_ms"] for s in self._steps)
