"""Agent 类型到 runner 的对照表。

放在 `app/runners/` 而不是 `app/services/`，是为了让命令行工具也能用它：
`app/services/runner_service.py` 会连带导入 SQLAlchemy 和全部 ORM 模型，
而 `agentbench run` 不该为了跑一个 suite 就把数据库拉起来。
"""

from app.runners.http_adapter import HTTPRunner
from app.runners.langgraph_adapter import LangGraphRunner
from app.runners.openai_adapter import OpenAICompatibleRunner
from app.runners.python_fn_adapter import PythonFnRunner

ADAPTER_MAP = {
    "openai_compatible": OpenAICompatibleRunner,
    "http": HTTPRunner,
    "python_fn": PythonFnRunner,
    "langgraph": LangGraphRunner,
}
