import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
from agentbench.evaluators.llm_judge_evaluator import LLMJudgeEvaluator

FAKE_JUDGE_RESPONSE = json.dumps({
    "accuracy": 5,
    "hallucination": 4,
    "tool_correctness": 3,
    "expression_quality": 4,
    "reasoning": "回答准确，无明显幻觉，工具调用一般，表达通顺。",
})

class TestLLMJudgeEvaluator:
    @pytest.mark.asyncio
    async def test_evaluate_calls_llm_and_parses(self):
        evaluator = LLMJudgeEvaluator(
            base_url="http://fake",
            api_key="test",
            model="gpt-4.1",
        )

        with patch("agentbench.evaluators.llm_judge_evaluator.httpx.AsyncClient") as mock_cls:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": FAKE_JUDGE_RESPONSE}}],
                "usage": {"prompt_tokens": 200, "completion_tokens": 50},
            }
            mock_response.raise_for_status.return_value = None

            mock_post = AsyncMock(return_value=mock_response)
            mock_instance = AsyncMock()
            mock_instance.post = mock_post
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await evaluator.evaluate_async(
                agent_output="CLANNAD 是 2007 年 Kyoto Animation 制作的动画。",
                expected="返回 CLANNAD 信息",
                scoring_criteria="必须包含年份和制作公司",
            )

        assert result.judge_type == "llm"
        assert result.overall_score == 4.0
        assert result.details["accuracy"] == 5
        assert "准确" in result.reasoning

    @pytest.mark.asyncio
    async def test_evaluate_handles_llm_error(self):
        evaluator = LLMJudgeEvaluator(
            base_url="http://fake", api_key="test", model="gpt-4.1",
        )

        with patch("agentbench.evaluators.llm_judge_evaluator.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(side_effect=Exception("API error"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_instance

            result = await evaluator.evaluate_async(
                agent_output="test", expected="", scoring_criteria="",
            )

        assert result.overall_score == 0.0
        assert "API error" in result.reasoning

    @pytest.mark.asyncio
    async def test_parse_response_with_markdown_code_block(self):
        evaluator = LLMJudgeEvaluator(base_url="http://fake", api_key="test", model="test")
        content = """好的，以下是评分结果：
```json
{"accuracy": 4, "hallucination": 5, "tool_correctness": 3, "expression_quality": 4, "reasoning": "良好"}
```
"""
        scores = evaluator._parse_response(content)
        assert scores["accuracy"] == 4
        assert scores["hallucination"] == 5
        assert scores["reasoning"] == "良好"
