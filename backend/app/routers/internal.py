import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, verify_internal_token
from app.models.match import Room, Match, PlayerScore
from app.models.question import Question
from app.schemas.match import MatchWithQuestionsResponse, MatchScoreSubmit
from app.schemas.question import QuestionResponse
from app.schemas.room import RoomStatusUpdate

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(verify_internal_token)],
)

VALID_STATUSES = {"waiting", "in_progress", "finished"}


@router.post("/rooms/{code}/match", response_model=MatchWithQuestionsResponse, status_code=status.HTTP_201_CREATED)
async def create_match(code: str, db: AsyncSession = Depends(get_db)):
    """Called by the game-server to start a match. Selects questions, creates the Match record."""
    result = await db.execute(select(Room).where(Room.code == code.upper()))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.status != "waiting":
        raise HTTPException(status_code=409, detail=f"Room is already {room.status}")

    q = select(Question).order_by(func.random()).limit(room.question_count)
    if room.category:
        q = q.where(Question.category == room.category)
    questions = (await db.execute(q)).scalars().all()

    if not questions:
        raise HTTPException(status_code=422, detail="No questions available for this room's category")

    match = Match(
        room_id=room.id,
        question_ids=[str(q.id) for q in questions],
    )
    room.status = "in_progress"
    db.add(match)
    await db.commit()
    await db.refresh(match)

    return MatchWithQuestionsResponse(
        id=match.id,
        room_id=match.room_id,
        questions=[QuestionResponse.model_validate(q) for q in questions],
        started_at=match.started_at,
    )


@router.patch("/rooms/{code}/status", status_code=status.HTTP_204_NO_CONTENT)
async def update_room_status(
    code: str,
    body: RoomStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status '{body.status}'")
    result = await db.execute(select(Room).where(Room.code == code.upper()))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    room.status = body.status
    await db.commit()


@router.post("/matches/{match_id}/scores", status_code=status.HTTP_201_CREATED)
async def submit_scores(
    match_id: uuid.UUID,
    payload: MatchScoreSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Called by the game-server at game end to persist per-player scores."""
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.ended_at:
        raise HTTPException(status_code=409, detail="Scores already submitted for this match")

    for entry in payload.scores:
        db.add(PlayerScore(
            match_id=match_id,
            user_id=entry.user_id,
            total_score=entry.total_score,
            answers=[a.model_dump() for a in entry.answers],
        ))

    match.ended_at = datetime.now(timezone.utc)

    room_result = await db.execute(select(Room).where(Room.id == match.room_id))
    room = room_result.scalar_one_or_none()
    if room:
        room.status = "finished"

    await db.commit()
