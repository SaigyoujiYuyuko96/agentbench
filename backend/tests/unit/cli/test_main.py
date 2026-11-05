import pytest

from agentbench.cli.main import main


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
    from agentbench.runners.base import AgentRunner, RunResult
    import agentbench.cli.runner as cli_runner

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

    def test_exits_two_when_the_file_is_not_utf8(self, tmp_path, capsys):
        # A suite saved by a Chinese Windows editor is GBK. Letting the
        # UnicodeDecodeError escape gives exit 1, which means "cases failed" —
        # a lie, since nothing ran.
        suite = tmp_path / "gbk.yaml"
        suite.write_bytes("agent:\n  type: http\n  名字: 值\n".encode("gbk"))

        code = main(["run", str(suite)])

        assert code == 2
        assert "UTF-8" in capsys.readouterr().err

    def test_exits_two_when_given_a_directory(self, tmp_path, capsys):
        code = main(["run", str(tmp_path)])

        assert code == 2
        assert "directory" in capsys.readouterr().err.lower()

    def test_exits_two_when_the_report_cannot_be_written(self, tmp_path, fake_runner, capsys):
        # The cases all passed, but CI would see exit 1 and blame the agent.
        # Blame the path instead.
        suite = tmp_path / "suite.yaml"
        suite.write_text(SUITE, encoding="utf-8")
        blocker = tmp_path / "blocked"
        blocker.write_text("not a directory", encoding="utf-8")

        code = main(["run", str(suite), "--report", str(blocker / "report.md")])

        assert code == 2
        assert "report" in capsys.readouterr().err.lower()


class TestConsoleEncoding:
    def test_a_passing_suite_still_exits_zero_on_a_gbk_console(
        self, tmp_path, monkeypatch
    ):
        # Windows cmd is GBK. An answer containing an emoji used to make print()
        # raise UnicodeEncodeError, turning a 1/1 pass into exit 1.
        from agentbench.runners.base import AgentRunner, RunResult
        import agentbench.cli.runner as cli_runner

        class Emoji(AgentRunner):
            async def run(self, test_input):
                return RunResult(output=f"{test_input} 😀 通过")

        monkeypatch.setitem(cli_runner.ADAPTER_MAP, "http", Emoji)
        monkeypatch.setattr("sys.stdout", _GbkConsole())
        suite = tmp_path / "suite.yaml"
        suite.write_text(SUITE, encoding="utf-8")

        code = main(["run", str(suite)])

        assert code == 0


class _GbkConsole:
    """sys.stdout 的替身：写进去的每个字符都必须能被 GBK 编码。

    和 Windows 中文控制台一样，编不了就抛 UnicodeEncodeError。真实终端上这
    个异常会从 print() 冒出来，把退出码从 0 变成 1。
    """

    encoding = "gbk"
    _buffer = ""

    def write(self, text):
        if not isinstance(text, str):
            raise TypeError(f"expected str, got {type(text).__name__}")
        text.encode("gbk")
        self._buffer += text

    def flush(self):
        pass


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
