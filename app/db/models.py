"""SQLAlchemy ORM models.

Each pipeline stage is persisted and linked by foreign key so past calls are
queryable: transcript -> extraction -> generated_output. Structured payloads are
stored as JSONB to stay flexible without rigid columns.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime


class Base(DeclarativeBase):
    pass


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(16))  # "audio" | "text"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    extractions: Mapped[list["Extraction"]] = relationship(
        back_populates="transcript", cascade="all, delete-orphan"
    )


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transcript_id: Mapped[int] = mapped_column(
        ForeignKey("transcripts.id", ondelete="CASCADE"), index=True
    )
    data: Mapped[dict] = mapped_column(JSONB)
    model: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    transcript: Mapped["Transcript"] = relationship(back_populates="extractions")
    outputs: Mapped[list["GeneratedOutput"]] = relationship(
        back_populates="extraction", cascade="all, delete-orphan"
    )


class GeneratedOutput(Base):
    __tablename__ = "generated_outputs"

    id: Mapped[int] = mapped_column(primary_key=True)
    extraction_id: Mapped[int] = mapped_column(
        ForeignKey("extractions.id", ondelete="CASCADE"), index=True
    )
    crm: Mapped[dict] = mapped_column(JSONB)
    tasks: Mapped[dict] = mapped_column(JSONB)  # {"tasks": [...]}
    email: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    extraction: Mapped["Extraction"] = relationship(back_populates="outputs")
