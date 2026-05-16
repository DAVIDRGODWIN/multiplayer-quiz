import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_admin
from app.models.question import Question
from app.models.user import User
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionResponse

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=list[QuestionResponse])
async def list_questions(
    category: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = select(Question).offset(skip).limit(limit)
    if category:
        q = q.where(Question.category == category)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    question = Question(**payload.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(question, field, value)
    await db.commit()
    await db.refresh(question)
    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    await db.delete(question)
    await db.commit()
