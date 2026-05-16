import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.question import QuestionResponse


class AnswerRecord(BaseModel):
    question_id: uuid.UUID
    score: int
    elapsed_seconds: float
    correct: bool


class PlayerScoreSubmit(BaseModel):
    user_id: uuid.UUID
    total_score: int
    answers: list[AnswerRecord]


class MatchScoreSubmit(BaseModel):
    scores: list[PlayerScoreSubmit]


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_id: uuid.UUID
    question_ids: list[str]
    started_at: datetime
    ended_at: Optional[datetime]


class MatchWithQuestionsResponse(BaseModel):
    """Returned to the game-server on match creation; includes full questions with correct answers."""
    id: uuid.UUID
    room_id: uuid.UUID
    questions: list[QuestionResponse]
    started_at: datetime


class PlayerScoreResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    total_score: int
    answers: list[AnswerRecord]


class LeaderboardEntry(BaseModel):
    username: str
    total_score: int
    match_id: uuid.UUID
    ended_at: Optional[datetime]
