from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "AI Workplace Safety Monitoring System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    MODEL_PATH: str = "ai/best.pt"
    CONFIDENCE_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.45
    IMAGE_SIZE: int = 640

    MAX_UPLOAD_SIZE_MB: int = 10

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 120
    RATE_LIMIT_DETECTION_PER_MINUTE: int = 60
    RATE_LIMIT_FRAME_PER_MINUTE: int = 600

    TRUST_PROXY_HEADERS: bool = False

    DATABASE_URL: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        if not self.DEBUG:
            if "*" in self.allowed_origins_list:
                raise ValueError(
                    "ALLOWED_ORIGINS tidak boleh mengandung '*' saat DEBUG=False."
                )
            if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
                raise ValueError(
                    "DATABASE_URL masih menunjuk ke localhost saat DEBUG=False."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()