from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: PostgresDsn
    db_test_url: PostgresDsn

    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None

    pgadmin_default_email: str | None = None
    pgadmin_default_password: str | None = None
    pgadmin_listen_port: str | None = None

    pythonpath: str | None = None

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings
