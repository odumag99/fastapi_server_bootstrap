"""애플리케이션 공통 예외 + FastAPI 예외 핸들러.

도메인/애플리케이션 레이어는 HTTP 를 모른다. 대신 AppError 를 던지고,
여기서 HTTP 응답으로 변환한다.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """모든 도메인/애플리케이션 예외의 베이스."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
