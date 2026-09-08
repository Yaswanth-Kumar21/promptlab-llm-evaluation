"""
EvaluationResult ORM model.

Stores the output of each evaluator (accuracy, relevance, tone, etc.)
for one experiment run.

Each row represents one metric for one experiment.
This normalised design makes it easy to add new metrics without schema changes.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    experiment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which evaluator produced this result
    # e.g. "accuracy", "relevance", "tone", "safety", "json_validity"
    metric: Mapped[str] = mapped_column(String(50), nullable=False)

    score: Mapped[float] = mapped_column(Float, nullable=False)   # 0.0 – 100.0
    passed: Mapped[bool] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[str] = mapped_column(Text, default="")

    # Method used: "deterministic" | "llm_judge" | "schema_check" | "semantic"
    evaluation_method: Mapped[str] = mapped_column(String(50), default="deterministic")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship(  # type: ignore[name-defined]
        "Experiment", back_populates="evaluation_results"
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationResult metric={self.metric!r} "
            f"score={self.score} passed={self.passed}>"
        )
