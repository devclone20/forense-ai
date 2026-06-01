from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://forense_app:dev_only_password@localhost:5432/forense_ai"
    database_url_sync: str = "postgresql://forense_app:dev_only_password@localhost:5432/forense_ai"

    # Security
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    audit_hmac_key: str = "CHANGE_ME_AUDIT_HMAC_KEY"

    # Application
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
