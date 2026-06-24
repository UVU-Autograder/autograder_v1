from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="sqlite+pysqlite:///:memory:",
        validation_alias="DATABASE_URL",
    )
    artifact_storage_dir: str = Field(
        default="data/artifacts",
        validation_alias="ARTIFACT_STORAGE_DIR",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="CELERY_BROKER_URL",
    )
    judge0_url: str = Field(default="http://localhost:2358", validation_alias="JUDGE0_URL")
    judge0_auth_token: str | None = Field(default=None, validation_alias="JUDGE0_AUTH_TOKEN")
    judge0_language_id: int = Field(default=71, ge=1, validation_alias="JUDGE0_LANGUAGE_ID")
    judge0_max_concurrent: int = Field(default=2, ge=1, validation_alias="JUDGE0_MAX_CONCURRENT")
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
    jwt_secret: str = Field(
        default="dev_fallback_secret_longer_than_32_characters_for_security_compliance",
        validation_alias="JWT_SECRET",
    )

    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, ge=1, validation_alias="JWT_EXPIRATION_HOURS")
    enable_mock_login: bool = Field(default=False, validation_alias="ENABLE_MOCK_LOGIN")
    sandbox_use_celery: bool = Field(default=False, validation_alias="SANDBOX_USE_CELERY")
    azure_openai_api_key: str | None = Field(default=None, validation_alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str | None = Field(default=None, validation_alias="AZURE_OPENAI_ENDPOINT")
    repo_root: str | None = Field(default=None, validation_alias="REPO_ROOT")

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def artifact_storage_path(self) -> Path:
        path = Path(self.artifact_storage_dir)
        if not path.is_absolute():
            # Make relative to backend root directory
            backend_dir = Path(__file__).resolve().parents[2]
            path = (backend_dir / path).resolve()
        return path

    @property
    def mock_login_enabled(self) -> bool:
        return self.enable_mock_login or self.is_sqlite


@lru_cache
def get_settings() -> Settings:
    return Settings()
