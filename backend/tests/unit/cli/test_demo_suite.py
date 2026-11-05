"""守住 `demo/suites/animepilot.yaml` 这份「能立刻跑」的 suite。

它是仓库唯一的演示入口，CI 里产出 artifact 的那一步跑的就是它。所以它必须
真能区分好坏：如果一条用例的断言词在它自己的输入里也出现过，一个只会把问题
复读一遍的 Agent 就能全过 —— 5.0 分毫无意义。
"""

from pathlib import Path

from agentbench.cli.runner import run_suite
from agentbench.cli.suite import load_suite
from agentbench.runners.base import AgentRunner, RunResult


DEMO_SUITE = Path(__file__).parents[4] / "demo" / "suites" / "animepilot.yaml"


class EchoAgent(AgentRunner):
    """只会把问题回显一遍。真正的区分能力全靠断言词挡住它。"""

    async def run(self, test_input):
        return RunResult(output=f"你说的是：{test_input}")


class TestDemoSuiteRejectsAnEcho:
    async def test_an_echo_agent_fails_every_case(self):
        suite = load_suite(DEMO_SUITE)

        outcomes = await run_suite(suite, runner_factory=lambda cfg: EchoAgent(cfg))

        passed = [o.case_id for o in outcomes if o.passed]
        assert not passed, (
            f"a do-nothing agent passed {passed}. The assertions in "
            f"{DEMO_SUITE.name} must name something the agent has to actually "
            f"know, not a word it can read off the question."
        )

    async def test_no_assertion_word_appears_in_its_own_input(self):
        # 直接查文件，不依赖回显行为：这条规则对任何「从输入里抄词」的答案都
        # 成立，不只是回显机。
        suite = load_suite(DEMO_SUITE)

        offenders = [
            (case.id, rule.value)
            for case in suite.cases
            for rule in case.rules
            if rule.type == "keyword_contains" and rule.value in case.input
        ]

        assert not offenders, (
            "these keywords are already in the question, so an agent could "
            f"pass by copying the input: {offenders}"
        )
