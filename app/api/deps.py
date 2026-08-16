import uuid
from collections.abc import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer()


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async for session in get_db():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
    )
    try:
        subject = decode_access_token(credentials.credentials)
        user = await UserRepository(session).get_by_id(uuid.UUID(subject))
    except (jwt.PyJWTError, ValueError) as exc:
        raise unauthorized from exc

    if user is None:
        raise unauthorized
    return user
