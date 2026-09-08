"""
Experiment ORM model.

An Experiment records one run of a prompt version against a dataset or
single input.  Every run is stored so users can compare results over time
(Core Feature 16 — Experiment Tracking).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), default="")
    prompt_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True
    )
    prompt_version_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("prompt_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # What was actually sent to the model
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Provider / model configuration at the time of the run
    provider: Mapped[str] = mapped_column(String(50), default="mock")
    model: Mapped[str] = mapped_column(String(100), default="")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024)

    # Raw response from the LLM
    response: Mapped[str] = mapped_column(Text, default="")
    response_raw: Mapped[str] = mapped_column(Text, default="")  # unparsed

    # Usage metrics
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Optional dataset reference
    dataset_name: Mapped[str] = mapped_column(String(255), default="")
    test_case_id: Mapped[str] = mapped_column(String(100), default="")

    # High-level outcome
    passed: Mapped[bool | None] = mapped_column(nullable=True)
    error: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship(  # type: ignore[name-defined]
        "Prompt", back_populates="experiments"
    )
    prompt_version: Mapped["PromptVersion"] = relationship(  # type: ignore[name-defined]
        "PromptVersion", back_populates="experiments"
    )
    evaluation_results: Mapped[list["EvaluationResult"]] = relationship(  # type: ignore[name-defined]
        "EvaluationResult", back_populates="experiment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Experiment id={self.id!r} provider={self.provider!r}>"
