"""Agent 类型到 runner 的对照表。

放在 `agentbench/runners/` 而不是 `agentbench/services/`，是为了让命令行工具也能用它：
`agentbench/services/runner_service.py` 会连带导入 SQLAlchemy 和全部 ORM 模型，
而 `agentbench run` 不该为了跑一个 suite 就把数据库拉起来。
"""

from agentbench.runners.http_adapter import HTTPRunner
from agentbench.runners.langgraph_adapter import LangGraphRunner
from agentbench.runners.openai_adapter import OpenAICompatibleRunner
from agentbench.runners.python_fn_adapter import PythonFnRunner

ADAPTER_MAP = {
    "openai_compatible": OpenAICompatibleRunner,
    "http": HTTPRunner,
    "python_fn": PythonFnRunner,
    "langgraph": LangGraphRunner,
}
