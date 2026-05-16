import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    host_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="waiting")  # waiting | in_progress | finished
    max_players: Mapped[int] = mapped_column(Integer, default=10)
    question_count: Mapped[int] = mapped_column(Integer, default=10)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id"), index=True)
    question_ids: Mapped[list] = mapped_column(JSON)  # ordered list of question UUID strings
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class PlayerScore(Base):
    __tablename__ = "player_scores"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    answers: Mapped[list] = mapped_column(JSON)  # [{question_id, score, elapsed_seconds, correct}]
