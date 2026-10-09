"""Identity HTTP 라우터: /auth/signup, /auth/login.

현재 v1. 호환 불가능한 변경이 필요하면 router_v2.py 를 추가하고
app/api/v2.py 에서 마운트한다 (URL 은 /api/v2/...).
"""

from fastapi import APIRouter, Depends, status

from app.modules.identity.dependencies import get_auth_service
from app.modules.identity.entities import Role
from app.modules.identity.schemas import (
    LoginRequest,
    SignUpRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.identity.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
)
async def sign_up(
    payload: SignUpRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await service.sign_up(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=Role(payload.role.value),
        grade=payload.grade,
    )
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="로그인 (JWT 발급)",
)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    tokens = await service.login(email=payload.email, password=payload.password)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )
