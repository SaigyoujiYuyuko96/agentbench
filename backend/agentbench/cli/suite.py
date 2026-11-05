"""读 suite 文件：一份 agent 配置，加一串有序的用例。

suite 文件是 `agentbench run` 的工作单元，刻意做得很小——格式见 `README.md`
——好让一个团队把它和自己描述的 Agent 一起放进仓库。
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from agentbench.evaluators.rule_evaluator import REGEX_MATCH, RULE_TYPES, RuleSpec
from agentbench.runners.registry import ADAPTER_MAP


class SuiteFileError(ValueError):
    """suite 文件缺了东西，或者自相矛盾。"""


# `${NAME}` 换成环境变量；`$$` 换成一个真的美元符号（没有这个转义就没法把
# 字面的 `${` 写进请求头）。
_ENV_REFERENCE = re.compile(r"\$(?P<escape>\$)|\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass
class Case:
    id: str
    title: str
    input: str
    rules: list[RuleSpec]


@dataclass
class Suite:
    agent_type: str
    agent_config: dict
    cases: list[Case] = field(default_factory=list)


def load_suite(path: str | Path) -> Suite:
    path = Path(path)
    text = _read_text(path)
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SuiteFileError(f"Suite file is not valid YAML: {exc}") from None

    if not isinstance(raw, dict):
        raise SuiteFileError("Suite file must be a mapping at the top level.")

    agent_type, agent_config = _read_agent(raw.get("agent"))
    cases = _read_cases(raw.get("cases"))
    _reject_duplicate_ids(cases)

    return Suite(agent_type=agent_type, agent_config=agent_config, cases=cases)


def _read_text(path: Path) -> str:
    """读文件，并把所有「读不了」都变成退出码 2。

    放任 UnicodeDecodeError 往外跑，退出码就是 1 —— 那是「用例没过」的意思，
    而实际上一个用例都没跑。存成 GBK 的中文 Windows 编辑器很常见，这条路上
    的报错必须自己接住。
    """
    if path.is_dir():
        raise SuiteFileError(f"Suite path is a directory, not a file: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SuiteFileError(f"Suite file not found: {path}") from None
    except UnicodeDecodeError:
        raise SuiteFileError(
            f"Suite file is not valid UTF-8: {path}. Re-save it as UTF-8."
        ) from None
    except OSError as exc:
        raise SuiteFileError(f"Suite file cannot be read: {exc}") from None


def _read_agent(agent) -> tuple[str, dict]:
    if not isinstance(agent, dict):
        raise SuiteFileError("Suite file needs an `agent:` mapping.")

    agent_type = agent.get("type")
    if agent_type not in ADAPTER_MAP:
        raise SuiteFileError(
            f"Unknown agent type: {agent_type!r}. "
            f"Known types: {', '.join(sorted(ADAPTER_MAP))}."
        )

    # 除 `type` 之外都是 runner 自己的配置，原样透传。
    config = {k: v for k, v in agent.items() if k != "type"}
    return agent_type, _expand_env(config, "the `agent:` section")


def _expand_env(value, where: str):
    """把 `${VAR}` 换成环境变量。

    放在 `agent:` 这一段里，是因为 token 只该出现在那儿（请求头）。suite 文件
    跟代码一起进仓库，所以它不能存密钥；CI 把密钥导出成环境变量，文件里只写
    引用。

    变量缺失时立刻报错。把 `${MY_API_TOKEN}` 原样发给服务器，会变成三层之外
    的一个 401，排查成本远高于在这里停住。
    """
    if isinstance(value, str):
        def replace(match: re.Match) -> str:
            if match.group("escape"):
                return "$"
            name = match.group("name")
            try:
                return os.environ[name]
            except KeyError:
                raise SuiteFileError(
                    f"{where} references ${{{name}}}, which is not set in the "
                    f"environment. Export it before running the suite."
                ) from None

        return _ENV_REFERENCE.sub(replace, value)
    if isinstance(value, dict):
        return {k: _expand_env(v, where) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v, where) for v in value]
    return value


def _read_cases(cases) -> list[Case]:
    if not isinstance(cases, list) or not cases:
        raise SuiteFileError("Suite file needs a non-empty `cases:` list.")

    parsed = []
    for index, entry in enumerate(cases, start=1):
        where = f"case #{index}"
        if not isinstance(entry, dict):
            raise SuiteFileError(f"{where} must be a mapping.")

        case_id = entry.get("id")
        if not case_id:
            raise SuiteFileError(f"{where} has no `id`.")
        where = f"case {case_id!r}"

        for key in ("title", "input"):
            if not entry.get(key):
                raise SuiteFileError(f"{where} has no `{key}`.")

        rules = _read_rules(entry.get("rules"), where)
        parsed.append(
            Case(
                id=str(case_id),
                title=str(entry["title"]),
                input=str(entry["input"]),
                rules=rules,
            )
        )
    return parsed


def _read_rules(rules, where: str) -> list[RuleSpec]:
    if not isinstance(rules, list) or not rules:
        raise SuiteFileError(f"{where} has no `rules`; a case with no rules cannot fail.")

    parsed = []
    for rule in rules:
        if not isinstance(rule, dict) or len(rule) != 1:
            raise SuiteFileError(
                f"{where} has a rule that is not a single-key mapping: {rule!r}"
            )
        (rule_type, value), = rule.items()
        if rule_type not in RULE_TYPES:
            raise SuiteFileError(
                f"{where} uses unknown rule {rule_type!r}. "
                f"Known rules: {', '.join(sorted(RULE_TYPES))}."
            )
        if rule_type == REGEX_MATCH:
            _compile_regex(str(value), where)
        parsed.append(RuleSpec(type=rule_type, value=str(value)))
    return parsed


def _compile_regex(pattern: str, where: str) -> None:
    """在读取时就把正则编一次。

    这是唯一能「快速失败」的地方：留到跑评测时再编，坏正则会在第一个答出话
    来的用例上抛出 re.error，退出码就不是约定的 2 而是一屏 traceback 了。
    """
    try:
        re.compile(pattern)
    except re.error as exc:
        raise SuiteFileError(f"{where} has an invalid regex {pattern!r}: {exc}") from None


def _reject_duplicate_ids(cases: list[Case]) -> None:
    seen, duplicates = set(), []
    for case in cases:
        if case.id in seen:
            duplicates.append(case.id)
        seen.add(case.id)
    if duplicates:
        raise SuiteFileError(
            f"Suite file has duplicate case ids: {', '.join(duplicates)}. "
            "Ids are what the report keys on, so they must be unique."
        )
