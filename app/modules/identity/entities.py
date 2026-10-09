"""Identity 도메인: 엔티티 · 값 객체 · 도메인 예외.

프레임워크/DB/보안 라이브러리에 의존하지 않는 순수 파이썬.
비밀번호 해싱은 서비스/인프라의 책임이므로 엔티티는 이미 해싱된
`hashed_password` 만 보관한다.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.core.exceptions import AppError

# ── 값 객체 ──────────────────────────────────────────


class Role(str, Enum):
    ADMIN = "admin"      # 시스템 관리자
    OWNER = "owner"      # 학원장
    TEACHER = "teacher"  # 강사/보조강사
    STUDENT = "student"  # 학생 (기본값)


class ApprovalStatus(str, Enum):
    PENDING = "pending"    # 승인 대기 (기본값)
    APPROVED = "approved"  # 승인됨
    REJECTED = "rejected"  # 거절됨


# ── 엔티티 ──────────────────────────────────────────


@dataclass
class User:
    email: str
    hashed_password: str
    full_name: str
    role: Role = Role.STUDENT
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    grade: str | None = None
    academy_id: uuid.UUID | None = None
    class_id: uuid.UUID | None = None
    # 영속화 전에는 None, 저장 후 채워진다.
    id: uuid.UUID | None = field(default=None)
    created_at: datetime | None = field(default=None)

    @classmethod
    def register(
        cls,
        *,
        email: str,
        hashed_password: str,
        full_name: str,
        role: Role = Role.STUDENT,
        grade: str | None = None,
    ) -> "User":
        """신규 가입 사용자를 생성한다. 항상 승인 대기(pending) 상태로 시작."""
        return cls(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            approval_status=ApprovalStatus.PENDING,
            grade=grade,
        )


# ── 도메인 예외 ─────────────────────────────────────


class EmailAlreadyExistsError(AppError):
    status_code = 409
    code = "email_already_exists"

    def __init__(self, email: str) -> None:
        super().__init__(f"이미 가입된 이메일이에요: {email}")


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "invalid_credentials"

    def __init__(self) -> None:
        super().__init__("이메일 또는 비밀번호가 올바르지 않아요.")
