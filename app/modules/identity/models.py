"""Identity ORM 모델 (SQLAlchemy 2.0 typed mapping).

role / approval_status 는 String 으로 저장한다(값은 도메인 Enum 의 value).
PG enum 타입 대신 String 을 써서 마이그레이션을 단순하게 유지.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.identity.entities import ApprovalStatus, Role


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=Role.STUDENT.value)
    approval_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ApprovalStatus.PENDING.value
    )
    academy_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    class_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
