from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, InvalidCredentialsError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.learning_profile import LearningProfile
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def register(self, email: str, password: str) -> User:
        if await self._users.get_by_email(email) is not None:
            raise AlreadyExistsError("A user with this email already exists")

        user = User(email=email, password_hash=hash_password(password))
        user.learning_profile = LearningProfile(priority_goals=[])
        await self._users.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> str:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        return create_access_token(subject=str(user.id))
