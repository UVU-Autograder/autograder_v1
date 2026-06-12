from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="sqlite+pysqlite:///:memory:",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="CELERY_BROKER_URL",
    )
    judge0_url: str = Field(default="http://localhost:2358", validation_alias="JUDGE0_URL")
    judge0_auth_token: str | None = Field(default=None, validation_alias="JUDGE0_AUTH_TOKEN")
    sandbox_upload_limit: int = Field(default=5, ge=1, validation_alias="SANDBOX_UPLOAD_LIMIT")
    sandbox_upload_window_seconds: int = Field(
        default=3600,
        ge=1,
        validation_alias="SANDBOX_UPLOAD_WINDOW_SECONDS",
    )
    max_upload_bytes: int = Field(default=50 * 1024 * 1024, ge=1, validation_alias="MAX_UPLOAD_BYTES")
    default_max_files: int = Field(default=100, ge=1, validation_alias="DEFAULT_MAX_FILES")
    default_max_zip_size: int = Field(default=50 * 1024 * 1024, ge=1, validation_alias="DEFAULT_MAX_ZIP_SIZE")
    test_execution_timeout_seconds: int = Field(default=30, ge=1, validation_alias="TEST_EXECUTION_TIMEOUT_SECONDS")

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
