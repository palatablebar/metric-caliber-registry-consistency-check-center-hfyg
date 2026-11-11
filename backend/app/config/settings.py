"""Runtime configuration — every field is overridable by the env var of the same name."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # --- database ---
    DB_NAME: str = "metricd_db"
    DB_USER: str = "metricd_user"
    DB_PASSWORD: str = "metricd_pwd"
    DB_ROOT_PASSWORD: str = "metricd_root_pwd"
    DB_HOST: str = "db"
    DB_PORT: int = 3306

    # --- auth ---
    JWT_SECRET: str = "metricd_dev_secret_change_me_2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8

    # --- infra ---
    REDIS_URL: str = "redis://redis:6379/0"
    ARTIFACT_DIR: str = "/data/artifacts"

    # --- limits ---
    CHECK_DAILY_QUOTA: int = 40
    RATE_WINDOW_SECONDS: int = 60
    RATE_WINDOW_MAX: int = 120
    CHECK_LOCK_TTL_SECONDS: int = 120

    # --- demo ---
    SEED_DEMO: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
