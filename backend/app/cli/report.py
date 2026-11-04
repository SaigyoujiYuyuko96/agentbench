"""把跑完的结果变成 CI 里能贴出来的 markdown。

两种读者都要照顾：扫一眼 pull request 评论的人，和只想知道「有没有挂」的
构建步骤。表格服务前者，摘要行服务后者。

标记刻意用 ASCII（PASS / FAIL）而不是 ✅ / ❌：Windows 的 GBK 控制台编码
不了那些符号，`print` 会抛 UnicodeEncodeError，退出码就从约定的 0/1/2 变成
一屏 traceback。
"""

from app.cli.runner import RunOutcome

# 答案可能很长；滚动好几屏的评论会被折叠、被无视，比截断更糟。
MAX_ANSWER_CHARS = 120


def summarize(outcomes: list[RunOutcome]) -> str:
    """`3/4 cases passed · average 4.2/5.0` —— 报告头部和 --quiet 共用这一行。"""
    passed = sum(1 for o in outcomes if o.passed)
    total = len(outcomes)
    average = sum(o.score for o in outcomes) / total if total else 0.0
    return f"{passed}/{total} cases passed · average {average:.1f}/5.0"


def render_markdown(outcomes: list[RunOutcome], *, suite_name: str) -> str:
    lines = [
        f"## AgentBench — {suite_name}",
        "",
        f"**{summarize(outcomes)}**",
        "",
        "| | Case | Score | Time | Agent output |",
        "|---|---|---|---|---|",
    ]

    for outcome in outcomes:
        mark = "PASS" if outcome.passed else "FAIL"
        lines.append(
            f"| {mark} | {_cell(outcome.case_id)} — {_cell(outcome.title)} "
            f"| {outcome.score:.1f} | {outcome.duration_ms}ms | {_answer_cell(outcome)} |"
        )

    failures = [o for o in outcomes if not o.passed]
    if failures:
        lines += ["", "### Failures", ""]
        for outcome in failures:
            reason = outcome.error or outcome.reasoning
            lines.append(f"- **{_cell(outcome.case_id)}** — {_cell(reason)}")
            lines.append(f"  - asked: {_cell(outcome.input)}")

    return "\n".join(lines)


def _answer_cell(outcome: RunOutcome) -> str:
    if outcome.error:
        return _cell(f"error: {outcome.error}")
    text = outcome.output.replace("\n", " ").strip()
    if not text:
        return _cell("(empty answer)")
    if len(text) > MAX_ANSWER_CHARS:
        text = text[: MAX_ANSWER_CHARS - 1] + "…"
    return _cell(text)


def _cell(text: str) -> str:
    """把一个值压成一行，并且留在同一个表格单元格里。

    转义竖线是为了不让表格断行。合并换行同样要紧：httpx 的错误会带第二行
    指向状态码文档，那个裸换行会提前结束表格行，把一段碎片留在文档里。
    """
    return " ".join(str(text).split()).replace("|", "\\|")
