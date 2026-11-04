import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.runners.http_adapter import HTTPRunner

class TestHTTPRunner:
    @pytest.mark.asyncio
    async def test_run_posts_to_endpoint(self):
        runner = HTTPRunner({
            "endpoint": "http://localhost:9000/chat",
            "method": "POST",
            "headers": {"X-API-Key": "test"},
        })
        mock_response_data = {
            "output": "你好，我是 Agent 回复。",
            "trace": [
                {"step_type": "intent_detection", "name": "Intent", "latency_ms": 50, "status": "success"},
            ],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None

        with patch("app.runners.http_adapter.httpx.AsyncClient") as mock_cls:
            mock_request = AsyncMock(return_value=mock_response)
            mock_instance = AsyncMock()
            mock_instance.request = mock_request
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await runner.run("你好")

        assert "Agent 回复" in result.output
        steps = result.collector.get_steps()
        assert len(steps) >= 1

    @pytest.mark.asyncio
    async def test_run_handles_connection_error(self):
        runner = HTTPRunner({"endpoint": "http://localhost:9999/chat"})

        with patch("app.runners.http_adapter.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(side_effect=Exception("Connection refused"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await runner.run("测试")

        assert result.error is not None
