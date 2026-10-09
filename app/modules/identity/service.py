"""인증/회원 서비스 (유스케이스).

오케스트레이션만 담당: 도메인 규칙은 엔티티에, 영속화는 리포지토리에 위임하고,
비밀번호 해싱/토큰 발급은 core.security 를 직접 사용한다.
"""

from dataclasses import dataclass

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.modules.identity.entities import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    Role,
    User,
)
from app.modules.identity.repository import UserRepository


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def sign_up(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        role: Role = Role.STUDENT,
        grade: str | None = None,
    ) -> User:
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyExistsError(email)

        user = User.register(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            grade=grade,
        )
        return await self._users.add(user)

    async def login(self, *, email: str, password: str) -> TokenPair:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            # 사용자 존재 여부를 노출하지 않도록 동일한 에러로 처리.
            raise InvalidCredentialsError()

        subject = str(user.id)
        return TokenPair(
            access_token=create_access_token(subject),
            refresh_token=create_refresh_token(subject),
        )
