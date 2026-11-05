from agentbench.cli.report import render_markdown, summarize
from agentbench.cli.runner import RunOutcome


def _outcome(case_id, score, passed, output="some answer", error=None):
    return RunOutcome(
        case_id=case_id,
        title=f"title of {case_id}",
        input=f"ask {case_id}",
        output=output,
        score=score,
        passed=passed,
        reasoning="1/1 rules passed." if passed else "0/1 rules passed.",
        duration_ms=12,
        error=error,
    )


class TestSummarize:
    def test_counts_passes_and_averages(self):
        line = summarize([_outcome("a", 5.0, True), _outcome("b", 3.0, False)])

        assert line.startswith("1/2")
        assert "4.0/5.0" in line

    def test_survives_an_empty_run(self):
        assert summarize([]).startswith("0/0")


class TestRenderMarkdown:
    def test_puts_a_row_per_case_and_the_average(self):
        md = render_markdown(
            [_outcome("a", 5.0, True), _outcome("b", 3.0, False)],
            suite_name="demo",
        )

        assert "| a —" in md
        assert "| b —" in md
        assert "4.0" in md, "average of 5.0 and 3.0"

    def test_marks_failures_so_they_are_visible_at_a_glance(self):
        md = render_markdown(
            [_outcome("good", 5.0, True), _outcome("bad", 1.0, False)],
            suite_name="demo",
        )

        assert md.count("| PASS |") == 1
        assert md.count("| FAIL |") == 1

    def test_stays_within_what_a_gbk_console_can_print(self):
        # A ✅/❌ here raises UnicodeEncodeError on a GBK console and turns the
        # documented 0/1/2 exit codes into a traceback. Encoding is the real
        # assertion; listing "allowed" characters would just drift.
        md = render_markdown(
            [_outcome("good", 5.0, True), _outcome("bad", 1.0, False)],
            suite_name="demo",
        )

        md.encode("gbk")

    def test_escapes_pipes_so_a_table_row_cannot_break(self):
        md = render_markdown(
            [_outcome("a", 5.0, True, output="one | two")],
            suite_name="demo",
        )

        rows = [ln for ln in md.splitlines() if "| a —" in ln]
        assert len(rows) == 1
        assert "one \\| two" in rows[0]

    def test_shows_the_error_instead_of_pretending_there_was_an_answer(self):
        md = render_markdown(
            [_outcome("a", 1.0, False, output="", error="Connection refused")],
            suite_name="demo",
        )

        assert "Connection refused" in md

    def test_keeps_a_multi_line_error_inside_its_own_row_and_bullet(self):
        # httpx errors carry a second line pointing at the status code docs.
        error = "Client error '422'\nFor more information check: https://example.com"

        md = render_markdown(
            [_outcome("a", 1.0, False, output="", error=error)],
            suite_name="demo",
        )

        bullets = [ln for ln in md.splitlines() if ln.startswith("- **a**")]
        assert len(bullets) == 1, "the failure list must not grow a stray line"
        assert "For more information" in bullets[0]
        assert md.count("\n\n## ") <= 1

    def test_carries_the_case_title_so_a_reviewer_knows_what_it_tested(self):
        md = render_markdown([_outcome("a", 5.0, True)], suite_name="demo")

        assert "title of a" in md

    def test_shows_how_long_each_case_took(self):
        md = render_markdown([_outcome("a", 5.0, True)], suite_name="demo")

        assert "12ms" in md

    def test_a_failure_says_what_was_asked_not_just_that_it_failed(self):
        md = render_markdown([_outcome("a", 1.0, False)], suite_name="demo")

        assert "ask a" in md, "the input belongs next to the reason"

    def test_truncates_a_long_answer_rather_than_bloating_the_comment(self):
        long_answer = "x" * 500

        md = render_markdown(
            [_outcome("a", 5.0, True, output=long_answer)], suite_name="demo"
        )

        assert long_answer not in md
        assert "…" in md

    def test_an_all_passing_suite_says_so(self):
        md = render_markdown(
            [_outcome("a", 5.0, True), _outcome("b", 5.0, True)], suite_name="demo"
        )

        assert "2/2" in md

    def test_states_the_suite_name(self):
        md = render_markdown([_outcome("a", 5.0, True)], suite_name="checkout-agent")

        assert "checkout-agent" in md
