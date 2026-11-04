from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.utils.trace_collector import TraceCollector


@dataclass
class RunResult:
    output: str = ""
    collector: TraceCollector = field(default_factory=TraceCollector)
    error: str | None = None


class AgentRunner(ABC):
    """Agent 执行适配器的抽象基类。

    子类必须实现 run 方法，将 Agent 的执行过程记录到 TraceCollector 中。
    """

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def run(self, test_input: str) -> RunResult:
        """执行 Agent 并返回结果 + trace。"""
        ...
