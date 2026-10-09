"""HTTP 요청/응답 스키마 (Pydantic).

API 계약은 도메인 모델과 분리한다 → 도메인 변경이 API 를 깨지 않도록.
버전 간 스키마가 달라지면 schemas_v2.py 로 분리한다.
"""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignUpRole(str, Enum):
    """가입 시 선택 가능한 역할. admin/owner 는 가입으로 만들 수 없다."""

    student = "student"
    teacher = "teacher"


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)
    role: SignUpRole = SignUpRole.student
    grade: str | None = Field(default=None, max_length=10)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    approval_status: str
    grade: str | None
    academy_id: uuid.UUID | None
    class_id: uuid.UUID | None
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
