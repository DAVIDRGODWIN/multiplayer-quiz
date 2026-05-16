import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    max_players: int = Field(default=10, ge=2, le=50)
    question_count: int = Field(default=10, ge=1, le=50)
    category: Optional[str] = None


class RoomStatusUpdate(BaseModel):
    status: str


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    host_id: uuid.UUID
    status: str
    max_players: int
    question_count: int
    category: Optional[str]
    created_at: datetime
