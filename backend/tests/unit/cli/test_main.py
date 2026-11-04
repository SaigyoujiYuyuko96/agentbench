import pytest

from app.cli.main import main


SUITE = """
agent:
  type: http
  endpoint: http://127.0.0.1:8003/api/agent/chat
  output_field: answer
cases:
  - id: passthrough
    title: 有答案就算过
    input: hi
    rules:
      - keyword_contains: hi
"""

FAILING_SUITE = """
agent:
  type: http
  endpoint: http://127.0.0.1:8003/api/agent/chat
  output_field: answer
cases:
  - id: impossible
    title: 永远不可能通过
    input: hi
    rules:
      - keyword_contains: a-string-that-is-never-returned
"""


@pytest.fixture
def fake_runner(monkeypatch):
    """把关掉真的 adapter 查找，换成一个把输入原样回显的 runner。"""
    from app.runners.base import AgentRunner, RunResult
    import app.cli.runner as cli_runner

    class Echo(AgentRunner):
        async def run(self, test_input):
            return RunResult(output=f"{test_input} ok")

    monkeypatch.setitem(cli_runner.ADAPTER_MAP, "http", Echo)


class TestExitCodes:
    def test_exits_zero_when_every_case_passes(self, tmp_path, fake_runner, capsys):
        suite = tmp_path / "suite.yaml"
        suite.write_text(SUITE, encoding="utf-8")

        code = main(["run", str(suite)])

        assert code == 0
        assert "1/1" in capsys.readouterr().out

    def test_exits_one_when_a_case_fails(self, tmp_path, fake_runner, capsys):
        suite = tmp_path / "suite.yaml"
        suite.write_text(FAILING_SUITE, encoding="utf-8")

        code = main(["run", str(suite)])

        assert code == 1

    def test_exits_two_on_a_malformed_suite(self, tmp_path, capsys):
        suite = tmp_path / "suite.yaml"
        suite.write_text("agent:\n  type: nope\n", encoding="utf-8")

        code = main(["run", str(suite)])

        assert code == 2
        assert "nope" in capsys.readouterr().err

    def test_exits_two_when_the_file_is_missing(self, tmp_path, capsys):
        code = main(["run", str(tmp_path / "absent.yaml")])

        assert code == 2
        assert "not found" in capsys.readouterr().err.lower()


class TestReportOutput:
    def test_writes_the_report_to_the_requested_path(self, tmp_path, fake_runner):
        suite = tmp_path / "suite.yaml"
        suite.write_text(SUITE, encoding="utf-8")
        report = tmp_path / "out" / "report.md"

        main(["run", str(suite), "--report", str(report)])

        assert report.exists()
        assert "AgentBench" in report.read_text(encoding="utf-8")

    def test_creates_the_parent_directory_of_the_report(self, tmp_path, fake_runner):
        suite = tmp_path / "suite.yaml"
        suite.write_text(SUITE, encoding="utf-8")
        report = tmp_path / "deeply" / "nested" / "report.md"

        main(["run", str(suite), "--report", str(report)])

        assert report.exists()

    def test_names_the_suite_after_the_file_by_default(self, tmp_path, fake_runner, capsys):
        suite = tmp_path / "checkout-agent.yaml"
        suite.write_text(SUITE, encoding="utf-8")

        main(["run", str(suite)])

        assert "checkout-agent" in capsys.readouterr().out
