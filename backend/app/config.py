from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholder values that are fine for local dev but must never reach a real
# deployment. Signing JWTs with a public default key means anyone can forge an
# admin token (full auth bypass); a known default admin password is the classic
# "default credentials" finding. We fail closed on both in production.
DEFAULT_SECRET_KEY = "dev-secret-change-me"
DEFAULT_ADMIN_PASSWORD = "admin123"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "development" (default) keeps the placeholders working for a quick local
    # run; set ENVIRONMENT=production to enforce the checks below.
    environment: str = "development"

    secret_key: str = DEFAULT_SECRET_KEY
    access_token_expire_minutes: int = 60 * 8  # a working day

    database_url: str = "sqlite:///./hardware_hub.db"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # Default admin, created on first boot so there is a way into the system.
    default_admin_email: str = "admin@booksy.com"
    default_admin_password: str = DEFAULT_ADMIN_PASSWORD

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

    @model_validator(mode="after")
    def _forbid_default_secrets_in_production(self) -> "Settings":
        """Fail closed: refuse to boot in production with placeholder secrets.

        OWASP ASVS V6 / V2 — no shipped default signing keys or credentials.
        Better to crash on startup than to silently run forgeable auth.
        """
        if not self.is_production:
            return self

        offenders = []
        if self.secret_key == DEFAULT_SECRET_KEY:
            offenders.append("SECRET_KEY (JWT signing key is the public default)")
        if self.default_admin_password == DEFAULT_ADMIN_PASSWORD:
            offenders.append("DEFAULT_ADMIN_PASSWORD (known default credentials)")

        if offenders:
            raise RuntimeError(
                "Refusing to start in production with insecure defaults: "
                + "; ".join(offenders)
                + ". Set them to strong, secret values via the environment."
            )
        return self


settings = Settings()
