"""`agentbench run <suite.yaml>` —— CI 的入口。

退出码才是流水线真正读的接口：
  0  所有用例都过
  1  suite 跑完了，但有东西没过
  2  suite 文件本身没法用
"""

import argparse
import asyncio
import sys
from pathlib import Path

from agentbench.cli.report import render_markdown, summarize
from agentbench.cli.runner import run_suite
from agentbench.cli.suite import SuiteFileError, load_suite

EXIT_OK = 0
EXIT_CASES_FAILED = 1
EXIT_BAD_SUITE = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentbench",
        description="跑一个 AgentBench suite 并打分。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="跑一个 suite 文件。")
    run.add_argument("suite", help="suite YAML 的路径。")
    run.add_argument(
        "--report",
        help="除了打到 stdout，也往这里写一份 markdown 报告。",
    )
    run.add_argument(
        "--quiet",
        action="store_true",
        help="只打摘要那一行，不打整张表。",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return asyncio.run(_run(args))


async def _run(args: argparse.Namespace) -> int:
    suite_path = Path(args.suite)
    try:
        suite = load_suite(suite_path)
    except SuiteFileError as exc:
        print(f"agentbench: {exc}", file=sys.stderr)
        return EXIT_BAD_SUITE

    # run_suite 自己挑 adapter，这里不用再解析一遍。
    outcomes = await run_suite(suite)

    report = render_markdown(outcomes, suite_name=suite_path.stem)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report + "\n", encoding="utf-8")

    print(summarize(outcomes) if args.quiet else report)

    return EXIT_OK if all(o.passed for o in outcomes) else EXIT_CASES_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
