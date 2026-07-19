from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60 * 8  # a working day

    database_url: str = "sqlite:///./hardware_hub.db"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    # Default admin, created on first boot so there is a way into the system.
    default_admin_email: str = "admin@booksy.com"
    default_admin_password: str = "admin123"


settings = Settings()
