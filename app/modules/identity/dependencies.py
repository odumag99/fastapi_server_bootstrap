"""라우터용 의존성 와이어링."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.identity.repository import UserRepository
from app.modules.identity.service import AuthService


def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    return AuthService(UserRepository(session))
