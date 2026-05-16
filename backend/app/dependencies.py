import uuid

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.auth import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token_data = verify_token(token)
    result = await db.execute(select(User).where(User.id == uuid.UUID(token_data.user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def verify_internal_token(x_internal_token: str = Header(...)) -> None:
    if x_internal_token != settings.internal_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal token")
