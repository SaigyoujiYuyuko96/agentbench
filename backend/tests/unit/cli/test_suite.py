import subprocess
import sys

import pytest

from app.cli.suite import SuiteFileError, load_suite


SUITE_TEXT = """
agent:
  type: http
  endpoint: http://127.0.0.1:8003/api/agent/chat
  output_field: answer
cases:
  - id: frieren
    title: 搜索葬送的芙莉莲
    input: 帮我找葬送的芙莉莲
    rules:
      - keyword_contains: 芙莉莲
      - keyword_not_contains: 抱歉
  - id: mushishi
    title: 虫师评价
    input: 虫师好看吗
    rules:
      - regex_match: 虫师|银古
"""


class TestLoadSuite:
    def test_reads_agent_config_and_ordered_cases(self, tmp_path):
        path = tmp_path / "suite.yaml"
        path.write_text(SUITE_TEXT, encoding="utf-8")

        suite = load_suite(path)

        assert suite.agent_type == "http"
        assert suite.agent_config["endpoint"] == "http://127.0.0.1:8003/api/agent/chat"
        assert [c.id for c in suite.cases] == ["frieren", "mushishi"]
        assert suite.cases[0].title == "搜索葬送的芙莉莲"
        assert suite.cases[0].input == "帮我找葬送的芙莉莲"

    def test_turns_rule_mappings_into_rule_specs(self, tmp_path):
        path = tmp_path / "suite.yaml"
        path.write_text(SUITE_TEXT, encoding="utf-8")

        suite = load_suite(path)

        rules = suite.cases[0].rules
        assert [(r.type, r.value) for r in rules] == [
            ("keyword_contains", "芙莉莲"),
            ("keyword_not_contains", "抱歉"),
        ]

    def test_rejects_a_case_with_no_rules(self, tmp_path):
        path = tmp_path / "suite.yaml"
        path.write_text(
            "agent:\n  type: http\n  endpoint: http://x\ncases:\n"
            "  - id: a\n    title: t\n    input: i\n",
            encoding="utf-8",
        )

        with pytest.raises(SuiteFileError, match="rules"):
            load_suite(path)

    def test_rejects_duplicate_case_ids(self, tmp_path):
        path = tmp_path / "suite.yaml"
        path.write_text(
            "agent:\n  type: http\n  endpoint: http://x\ncases:\n"
            "  - id: dup\n    title: a\n    input: i\n    rules:\n      - keyword_contains: x\n"
            "  - id: dup\n    title: b\n    input: j\n    rules:\n      - keyword_contains: y\n",
            encoding="utf-8",
        )

        with pytest.raises(SuiteFileError, match="duplicate"):
            load_suite(path)

    def test_rejects_an_unknown_agent_type(self, tmp_path):
        path = tmp_path / "suite.yaml"
        path.write_text(
            "agent:\n  type: carrier-pigeon\n  endpoint: http://x\ncases:\n"
            "  - id: a\n    title: t\n    input: i\n    rules:\n      - keyword_contains: x\n",
            encoding="utf-8",
        )

        with pytest.raises(SuiteFileError, match="carrier-pigeon"):
            load_suite(path)

    def test_rejects_an_invalid_regex_at_load_time(self, tmp_path):
        # Compiling at load time is the only place this can fail fast. Left to
        # evaluation, a bad pattern raises re.error on the first case whose
        # agent actually answers — exit 1 with a traceback instead of exit 2.
        path = tmp_path / "suite.yaml"
        path.write_text(
            "agent:\n  type: http\n  endpoint: http://x\ncases:\n"
            "  - id: a\n    title: t\n    input: i\n    rules:\n"
            "      - regex_match: '(unclosed'\n",
            encoding="utf-8",
        )

        with pytest.raises(SuiteFileError, match="invalid regex"):
            load_suite(path)


class TestStaysOffTheDatabase:
    def test_importing_the_cli_does_not_pull_in_sqlalchemy(self):
        # The README promises the CLI needs no database. Importing ADAPTER_MAP
        # from app.services.runner_service would drag SQLAlchemy and every ORM
        # model in with it, making that promise false.
        probe = (
            "import sys, app.cli.main; "
            "heavy = [m for m in ('sqlalchemy', 'aiosqlite', 'app.database') "
            "if m in sys.modules]; "
            "print(heavy)"
        )

        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            check=True,
        )

        assert result.stdout.strip() == "[]", result.stdout
