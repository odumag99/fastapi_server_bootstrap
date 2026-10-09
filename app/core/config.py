"""애플리케이션 설정.

pydantic-settings 로 .env / 환경변수에서 설정을 읽는다.
참고: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──
    APP_NAME: str = "MathKnot API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "local"
    DEBUG: bool = True

    # ── Database ──
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "mathknot"
    POSTGRES_PASSWORD: str = "mathknot"
    POSTGRES_DB: str = "mathknot"

    # ── JWT ──
    JWT_SECRET_KEY: str = "dev-only-secret-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    @property
    def database_url(self) -> str:
        """SQLAlchemy async 엔진용 DSN (asyncpg 드라이버)."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    """설정 싱글턴. lru_cache 로 프로세스당 한 번만 로드한다."""
    return Settings()
