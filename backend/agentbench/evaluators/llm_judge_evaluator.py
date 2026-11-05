import json
import re
import httpx
from agentbench.evaluators.base import BaseEvaluator, EvaluationResult

JUDGE_SYSTEM_PROMPT = """你是一个专业的 AI Agent 评测裁判。你的任务是评估 Agent 对用户问题的回答质量。

请严格按照以下四个维度打分（每项 1-5 分）：
1. accuracy（准确性）：回答是否准确回答了用户问题
2. hallucination（无幻觉）：回答中是否有编造的事实（5分=无幻觉，1分=严重幻觉）
3. tool_correctness（工具调用正确性）：如果涉及工具调用，参数和调用是否正确（无工具调用给 3 分）
4. expression_quality（表达质量）：中文表达是否通顺、专业、清晰

你必须以 JSON 格式返回评分结果，不要包含任何其他文字：
{"accuracy": N, "hallucination": N, "tool_correctness": N, "expression_quality": N, "reasoning": "简短的评分理由"}
"""

class LLMJudgeEvaluator(BaseEvaluator):
    def __init__(self, *, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def evaluate(
        self,
        *,
        agent_output: str,
        expected: str = "",
        scoring_criteria: str = "",
        run_steps: list[dict] | None = None,
    ) -> EvaluationResult:
        raise NotImplementedError("Use evaluate_async instead")

    async def evaluate_async(
        self,
        *,
        agent_output: str,
        expected: str = "",
        scoring_criteria: str = "",
        run_steps: list[dict] | None = None,
    ) -> EvaluationResult:
        user_prompt = self._build_prompt(agent_output, expected, scoring_criteria, run_steps)

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.1,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            scores = self._parse_response(content)

            overall = round(
                (scores["accuracy"] + scores["hallucination"] + scores["tool_correctness"] + scores["expression_quality"]) / 4, 1
            )

            return EvaluationResult(
                judge_type="llm",
                overall_score=overall,
                passed=overall >= 3.0,
                reasoning=scores.get("reasoning", ""),
                details=scores,
            )

        except Exception as e:
            return EvaluationResult(
                judge_type="llm",
                overall_score=0.0,
                passed=False,
                reasoning=f"LLM Judge error: {e}",
            )

    def _build_prompt(
        self,
        agent_output: str,
        expected: str,
        scoring_criteria: str,
        run_steps: list[dict] | None,
    ) -> str:
        parts = [
            "## 用户输入的问题",
            "（见下方期望行为描述）",
            "",
            "## Agent 的回答",
            agent_output,
        ]
        if expected:
            parts += ["", "## 期望行为", expected]
        if scoring_criteria:
            parts += ["", "## 评分标准", scoring_criteria]
        if run_steps:
            steps_summary = "\n".join(
                f"- {s.get('step_type', '?')} ({s.get('name', '')}): {s.get('status', '?')} - {s.get('latency_ms', 0)}ms"
                for s in run_steps
            )
            parts += ["", "## 调用链步骤", steps_summary]
        return "\n".join(parts)

    def _parse_response(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        match = re.search(r"\{[^}]+\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {"accuracy": 0, "hallucination": 0, "tool_correctness": 0, "expression_quality": 0, "reasoning": f"Failed to parse LLM response: {content[:200]}"}
