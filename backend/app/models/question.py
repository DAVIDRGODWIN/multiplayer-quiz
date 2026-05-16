import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(String(1000))
    correct_answer: Mapped[str] = mapped_column(String(500))
    # None = free-text question; list of strings = multiple choice
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    time_limit: Mapped[int] = mapped_column(Integer, default=30)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
