"""사용자 리포지토리 (구체 구현).

ORM 모델 <-> 도메인 엔티티 매핑을 여기서 처리한다. 도메인은 ORM 을 모른다.
트랜잭션 커밋은 세션 의존성(get_session)이 담당하므로 여기선 flush 까지만 한다.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.entities import ApprovalStatus, Role, User
from app.modules.identity.models import UserModel


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        hashed_password=model.hashed_password,
        full_name=model.full_name,
        role=Role(model.role),
        approval_status=ApprovalStatus(model.approval_status),
        grade=model.grade,
        academy_id=model.academy_id,
        class_id=model.class_id,
        created_at=model.created_at,
    )


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            role=user.role.value,
            approval_status=user.approval_status.value,
            grade=user.grade,
            academy_id=user.academy_id,
            class_id=user.class_id,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
