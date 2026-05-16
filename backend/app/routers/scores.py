import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.match import Match, PlayerScore
from app.models.user import User
from app.schemas.match import PlayerScoreResponse, AnswerRecord, LeaderboardEntry

router = APIRouter(tags=["scores"])


@router.get("/matches/{match_id}/scores", response_model=list[PlayerScoreResponse])
async def get_match_scores(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PlayerScore, User.username)
        .join(User, PlayerScore.user_id == User.id)
        .where(PlayerScore.match_id == match_id)
        .order_by(PlayerScore.total_score.desc())
    )
    return [
        PlayerScoreResponse(
            user_id=ps.user_id,
            username=username,
            total_score=ps.total_score,
            answers=[AnswerRecord(**a) for a in ps.answers],
        )
        for ps, username in result.all()
    ]


@router.get("/scores/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User.username, PlayerScore.total_score, PlayerScore.match_id, Match.ended_at)
        .join(User, PlayerScore.user_id == User.id)
        .join(Match, PlayerScore.match_id == Match.id)
        .where(Match.ended_at.isnot(None))
        .order_by(PlayerScore.total_score.desc())
        .limit(limit)
    )
    return [
        LeaderboardEntry(username=u, total_score=s, match_id=m, ended_at=e)
        for u, s, m, e in result.all()
    ]
