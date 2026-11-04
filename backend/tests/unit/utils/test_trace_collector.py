import pytest
import time
from app.utils.trace_collector import TraceCollector

class TestTraceCollector:
    def test_record_step(self):
        collector = TraceCollector()
        collector.record_step(
            step_type="intent_detection",
            name="IntentDetector",
            input_data={"query": "搜索动漫"},
            output_data={"intent": "search"},
            latency_ms=100,
            token_input=50,
            token_output=20,
            status="success",
        )
        steps = collector.get_steps()
        assert len(steps) == 1
        assert steps[0]["step_type"] == "intent_detection"
        assert steps[0]["latency_ms"] == 100

    def test_record_step_with_error(self):
        collector = TraceCollector()
        collector.record_step(
            step_type="llm_generation",
            name="LLMCall",
            input_data={},
            output_data={},
            latency_ms=5000,
            status="error",
            error_message="API timeout",
        )
        steps = collector.get_steps()
        assert steps[0]["status"] == "error"
        assert steps[0]["error_message"] == "API timeout"

    def test_sequence_auto_increment(self):
        collector = TraceCollector()
        collector.record_step(step_type="a", name="a", input_data={}, output_data={}, latency_ms=10, status="success")
        collector.record_step(step_type="b", name="b", input_data={}, output_data={}, latency_ms=10, status="success")
        steps = collector.get_steps()
        assert steps[0]["sequence"] == 1
        assert steps[1]["sequence"] == 2

    def test_to_run_step_dicts(self):
        collector = TraceCollector()
        collector.record_step(
            step_type="tool_call", name="SearchTool", input_data={"q": "x"},
            output_data={"result": "y"}, latency_ms=200, token_input=10, token_output=30,
            status="success",
        )
        dicts = collector.to_run_step_dicts(test_run_id=42)
        assert len(dicts) == 1
        assert dicts[0]["test_run_id"] == 42
        assert dicts[0]["sequence"] == 1

    def test_total_tokens(self):
        collector = TraceCollector()
        collector.record_step(step_type="a", name="a", token_input=10, token_output=20, latency_ms=1, status="success")
        collector.record_step(step_type="b", name="b", token_input=30, token_output=40, latency_ms=1, status="success")
        assert collector.total_tokens() == 100

    def test_total_latency_ms(self):
        collector = TraceCollector()
        collector.record_step(step_type="a", name="a", latency_ms=100, status="success")
        collector.record_step(step_type="b", name="b", latency_ms=200, status="success")
        assert collector.total_latency_ms() == 300
