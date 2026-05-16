import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class QuestionCreate(BaseModel):
    text: str
    correct_answer: str
    options: Optional[list[str]] = None
    time_limit: int = 30
    category: Optional[str] = None


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    correct_answer: Optional[str] = None
    options: Optional[list[str]] = None
    time_limit: Optional[int] = None
    category: Optional[str] = None


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    correct_answer: str
    options: Optional[list[str]]
    time_limit: int
    category: Optional[str]
    created_at: datetime


class QuestionPublic(BaseModel):
    """Question without correct_answer — safe to broadcast to players during a game."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    options: Optional[list[str]]
    time_limit: int
    category: Optional[str]
