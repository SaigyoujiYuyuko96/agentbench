from agentbench.cli.runner import run_suite
from agentbench.cli.suite import Case, Suite
from agentbench.evaluators.rule_evaluator import RuleSpec
from agentbench.runners.base import AgentRunner, RunResult


class FakeRunner(AgentRunner):
    """Returns whatever the test told it to, keyed by input text."""

    def __init__(self, config, answers):
        super().__init__(config)
        self.answers = answers
        self.calls = []

    async def run(self, test_input):
        self.calls.append(test_input)
        return RunResult(output=self.answers.get(test_input, ""))


def _suite(*cases):
    return Suite(agent_type="http", agent_config={"endpoint": "http://x"}, cases=list(cases))


def _case(case_id, text, *rules):
    return Case(
        id=case_id,
        title=case_id,
        input=text,
        rules=[RuleSpec(type=t, value=v) for t, v in rules],
    )


class TestRunSuite:
    async def test_records_one_outcome_per_case_in_order(self):
        suite = _suite(
            _case("a", "first", ("keyword_contains", "alpha")),
            _case("b", "second", ("keyword_contains", "beta")),
        )
        runner = FakeRunner({}, {"first": "alpha done", "second": "beta done"})

        outcomes = await run_suite(suite, runner_factory=lambda cfg: runner)

        assert [o.case_id for o in outcomes] == ["a", "b"]
        assert [o.passed for o in outcomes] == [True, True]

    async def test_a_case_whose_answer_misses_the_rule_fails(self):
        suite = _suite(_case("a", "first", ("keyword_contains", "alpha")))
        runner = FakeRunner({}, {"first": "something else entirely"})

        (outcome,) = await run_suite(suite, runner_factory=lambda cfg: runner)

        assert outcome.passed is False
        assert outcome.score < 5.0

    async def test_a_runner_error_fails_the_case_without_raising(self):
        class Exploding(AgentRunner):
            async def run(self, test_input):
                return RunResult(output="", error="boom")

        suite = _suite(_case("a", "first", ("keyword_contains", "alpha")))

        (outcome,) = await run_suite(
            suite, runner_factory=lambda cfg: Exploding({})
        )

        assert outcome.passed is False
        assert outcome.error == "boom"

    async def test_the_agent_config_reaches_the_runner(self):
        seen = {}

        def factory(config):
            seen.update(config)
            return FakeRunner(config, {"first": "alpha"})

        suite = _suite(_case("a", "first", ("keyword_contains", "alpha")))
        await run_suite(suite, runner_factory=factory)

        assert seen == {"endpoint": "http://x"}

    async def test_an_empty_answer_fails_every_contains_rule(self):
        suite = _suite(_case("a", "first", ("keyword_not_contains", "sorry")))
        runner = FakeRunner({}, {"first": ""})

        (outcome,) = await run_suite(suite, runner_factory=lambda cfg: runner)

        assert outcome.passed is True, "not_contains passes on an empty answer"
        assert outcome.output == ""

    async def test_a_structured_answer_is_scored_as_text_not_crashed_on(self):
        # An HTTP agent is free to answer {"text": ..., "score": ...}. Today that
        # raises TypeError inside re.search and no report gets written at all.
        suite = _suite(_case("a", "first", ("keyword_contains", "alpha")))

        class Structured(AgentRunner):
            async def run(self, test_input):
                return RunResult(output={"text": "alpha in a nested dict", "score": 0.9})

        (outcome,) = await run_suite(suite, runner_factory=lambda cfg: Structured({}))

        assert "alpha" in outcome.output
        assert outcome.passed is True
