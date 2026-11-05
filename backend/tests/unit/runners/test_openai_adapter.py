import pytest
from unittest.mock import AsyncMock, Mock, patch
from agentbench.runners.openai_adapter import OpenAICompatibleRunner

class TestOpenAICompatibleRunner:
    @pytest.mark.asyncio
    async def test_run_records_trace(self):
        runner = OpenAICompatibleRunner({
            "endpoint": "http://fake-api/v1/chat/completions",
            "model": "gpt-4.1",
            "api_key": "test-key",
        })

        mock_response = {
            "choices": [{"message": {"content": "CLANNAD 是一部经典治愈系动画。"}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
        }

        with patch("agentbench.runners.openai_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock()
            mock_resp = Mock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client_instance

            result = await runner.run("推荐一部治愈系动画")

        assert "CLANNAD" in result.output
        assert result.error is None
        steps = result.collector.get_steps()
        assert len(steps) >= 1
        assert steps[0]["step_type"] == "llm_generation"
        assert steps[0]["token_usage_input"] == 50
        assert steps[0]["token_usage_output"] == 100

    @pytest.mark.asyncio
    async def test_run_handles_api_error(self):
        runner = OpenAICompatibleRunner({
            "endpoint": "http://fake-api/v1/chat/completions",
            "model": "gpt-4.1",
            "api_key": "test-key",
        })

        with patch("agentbench.runners.openai_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock()
            mock_resp = Mock()
            mock_resp.raise_for_status.side_effect = Exception("API Error")
            mock_resp.text = "Internal Server Error"
            mock_post.return_value = mock_resp
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client_instance

            result = await runner.run("测试")

        assert result.error is not None
        assert "API Error" in result.error
