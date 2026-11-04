"""不用数据库、不用 web server 也能跑完一个 suite。

web 那套把每次运行记进 SQLite 再通过 API 读回来；命令行不需要这些——CI 只要
答案和分数，然后退出。所以这个模块直接驱动同一批 runner 和 evaluator，结果
只留在内存里。
"""

import time
from dataclasses import dataclass, field
from typing import Callable

from app.cli.suite import Suite
from app.evaluators.rule_evaluator import RuleEvaluator
from app.runners.base import AgentRunner
from app.runners.registry import ADAPTER_MAP


@dataclass
class RunOutcome:
    case_id: str
    title: str
    input: str
    output: str = ""
    score: float = 1.0
    passed: bool = False
    reasoning: str = ""
    duration_ms: int = 0
    error: str | None = None


async def run_suite(
    suite: Suite,
    *,
    runner_factory: Callable[[dict], AgentRunner] | None = None,
) -> list[RunOutcome]:
    """每个用例跑一次并打分。单个用例出错不往外抛。"""
    factory = runner_factory or ADAPTER_MAP[suite.agent_type]
    runner = factory(dict(suite.agent_config))

    outcomes = []
    for case in suite.cases:
        started = time.monotonic()
        result = await runner.run(case.input)
        duration_ms = int((time.monotonic() - started) * 1000)

        outcome = RunOutcome(
            case_id=case.id,
            title=case.title,
            input=case.input,
            output=result.output,
            duration_ms=duration_ms,
        )

        if result.error is not None:
            outcome.score = 1.0
            outcome.passed = False
            outcome.reasoning = "The agent did not answer."
            outcome.error = result.error
            outcomes.append(outcome)
            continue

        evaluation = RuleEvaluator(case.rules).evaluate(
            agent_output=result.output,
            expected="",
            scoring_criteria="",
        )
        outcome.score = evaluation.overall_score
        outcome.passed = evaluation.passed
        outcome.reasoning = evaluation.reasoning
        outcomes.append(outcome)

    return outcomes
