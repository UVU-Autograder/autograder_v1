from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    database_url: str = Field(
        default="postgresql+psycopg://autograder:autograder_dev_password@127.0.0.1:5432/autograder",
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
    judge0_language_id: int = Field(default=711, ge=1, validation_alias="JUDGE0_LANGUAGE_ID")
    judge0_max_concurrent: int = Field(default=2, ge=1, validation_alias="JUDGE0_MAX_CONCURRENT")
    judge0_preinstalled_dependencies: str = Field(
        default="pillow,pygame,tabulate",
        validation_alias="JUDGE0_PREINSTALLED_DEPENDENCIES",
    )
    sandbox_upload_limit: int = Field(default=999999, ge=1, validation_alias="SANDBOX_UPLOAD_LIMIT")
    # Runs per client address per upload window; 0 turns it off (see sandbox/ip_limit.py
    # before enabling: the VPN or NAT can put a whole class behind one address).
    sandbox_ip_hourly_limit: int = Field(default=0, ge=0, validation_alias="SANDBOX_IP_HOURLY_LIMIT")
    sandbox_ip_allowlist: str = Field(default="", validation_alias="SANDBOX_IP_ALLOWLIST")
    sandbox_upload_window_seconds: int = Field(
        default=3600,
        ge=1,
        validation_alias="SANDBOX_UPLOAD_WINDOW_SECONDS",
    )
    max_upload_bytes: int = Field(default=50 * 1024 * 1024, ge=1, validation_alias="MAX_UPLOAD_BYTES")
    official_batch_limit: int = Field(default=200, ge=1, validation_alias="OFFICIAL_BATCH_LIMIT")
    official_unfinished_limit: int = Field(default=1000, ge=1, validation_alias="OFFICIAL_UNFINISHED_LIMIT")
    default_max_files: int = Field(default=100, ge=1, validation_alias="DEFAULT_MAX_FILES")
    default_max_zip_size: int = Field(default=50 * 1024 * 1024, ge=1, validation_alias="DEFAULT_MAX_ZIP_SIZE")
    test_execution_timeout_seconds: int = Field(default=30, ge=1, validation_alias="TEST_EXECUTION_TIMEOUT_SECONDS")
    jwt_secret: str = Field(
        default="dev_fallback_secret_longer_than_32_characters_for_security_compliance",
        validation_alias="JWT_SECRET",
    )

    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=60, ge=1, validation_alias="JWT_EXPIRATION_MINUTES")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    auth_provider: str = Field(default="mock", validation_alias="AUTH_PROVIDER")
    azure_ad_tenant_id: str | None = Field(default=None, validation_alias="AZURE_AD_TENANT_ID")
    azure_ad_client_id: str | None = Field(default=None, validation_alias="AZURE_AD_CLIENT_ID")
    enable_mock_login: bool = Field(default=False, validation_alias="ENABLE_MOCK_LOGIN")
    sandbox_use_celery: bool = Field(default=False, validation_alias="SANDBOX_USE_CELERY")
    # Show waiting students an anonymous count of submissions queued before theirs.
    # Off: a generic "other submissions are running" message instead.
    sandbox_show_queue_ahead: bool = Field(default=True, validation_alias="SANDBOX_SHOW_QUEUE_AHEAD")
    # AI feedback capacity. Measured on the Dell: ~16 simultaneous requests all finish
    # well under the 30 s model timeout. Requests beyond that wait (bounded) for a slot;
    # past the wait limit the student gets "busy, retrying" instead of a timeout.
    # The limit is per API process; the backend runs one uvicorn process.
    ai_max_concurrent: int = Field(default=16, ge=1, validation_alias="AI_MAX_CONCURRENT")
    ai_max_waiting: int = Field(default=24, ge=0, validation_alias="AI_MAX_WAITING")
    ai_max_wait_seconds: float = Field(default=20.0, gt=0, validation_alias="AI_MAX_WAIT_SECONDS")
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,https://autograder-frontend-mockup.vercel.app",
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    local_llm_api_key: str | None = Field(default="none", validation_alias="LOCAL_LLM_API_KEY")
    local_llm_endpoint: str | None = Field(default="http://127.0.0.1:8001/v1", validation_alias="LOCAL_LLM_ENDPOINT")
    local_llm_model: str = Field(default="cs1410-p3b", validation_alias="LOCAL_LLM_MODEL")
    # Which feedback prompt each served model was trained on, as "model=version,...".
    # Unlisted models (p3b, the base-model rollback) get prompts.PROMPT_VERSION (v8).
    # Same default as prompts.DEFAULT_PROMPT_VERSION_MAP (core settings do not import integrations).
    local_llm_prompt_versions: str = Field(default="cs1410-p4=v9", validation_alias="LOCAL_LLM_PROMPT_VERSIONS")
    repo_root: str | None = Field(default=None, validation_alias="REPO_ROOT")

    def prompt_version_for(self, model: str) -> str:
        """The prompt version ``model`` was trained on (see local_llm_prompt_versions)."""
        from app.integrations.ai.prompts import prompt_version_for

        return prompt_version_for(model, self.local_llm_prompt_versions)

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


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
        if self.environment == "production" or self.auth_provider == "microsoft":
            return False
        return self.enable_mock_login or self.environment in ("development", "test")

    def validate_production_security(self) -> None:
        """Validate production security invariants at startup."""
        if self.environment == "production" or self.auth_provider == "microsoft":
            if self.jwt_secret == "dev_fallback_secret_longer_than_32_characters_for_security_compliance":
                raise ValueError("Production mode requires an explicit, non-default JWT_SECRET.")
            if self.auth_provider == "microsoft" and not self.azure_ad_client_id:
                raise ValueError("AUTH_PROVIDER=microsoft requires AZURE_AD_CLIENT_ID to be set.")

    @property
    def preinstalled_dependency_names(self) -> set[str]:
        return {
            dependency.strip().lower()
            for dependency in self.judge0_preinstalled_dependencies.split(",")
            if dependency.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
