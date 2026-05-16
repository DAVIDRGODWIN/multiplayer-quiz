import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.match import Room
from app.models.user import User
from app.schemas.room import RoomCreate, RoomResponse

router = APIRouter(prefix="/rooms", tags=["rooms"])


def _generate_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


async def _unique_code(db: AsyncSession) -> str:
    for _ in range(10):
        code = _generate_code()
        result = await db.execute(select(Room).where(Room.code == code))
        if not result.scalar_one_or_none():
            return code
    raise RuntimeError("Failed to generate a unique room code after 10 attempts")


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    code = await _unique_code(db)
    room = Room(
        code=code,
        host_id=user.id,
        max_players=payload.max_players,
        question_count=payload.question_count,
        category=payload.category,
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Room).where(Room.status == "waiting"))
    return result.scalars().all()


@router.get("/{code}", response_model=RoomResponse)
async def get_room(
    code: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Room).where(Room.code == code.upper()))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room
