from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from agentbench.database import Base

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("test_runs.id"), nullable=False)
    judge_type: Mapped[str] = mapped_column(String(20), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tool_correctness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    expression_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    judge_reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rule_results: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
