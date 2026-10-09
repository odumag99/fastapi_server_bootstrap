"""API v1 라우터 집합.

각 바운디드 컨텍스트의 v1 라우터를 /api/v1 아래로 모은다.
호환 불가능한 변경이 생기면 v2.py 를 추가하고 /api/v2 로 별도 마운트한다.
"""

from fastapi import APIRouter

from app.modules.identity.router import router as identity_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(identity_router)
