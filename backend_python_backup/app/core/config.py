"""Application settings, loaded from environment variables and an optional ``.env`` file.

Lookup order (later wins): ``<repo>/.env`` -> ``backend/.env`` -> real environment variables.
Nothing secret is hard-coded; see ``.env.example`` at the repository root.
"""
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]  # .../backend
REPO_ROOT = BACKEND_DIR.parent

DEV_SECRET_KEY = "dev-only-insecure-secret-key-change-me-0123456789"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # the shared .env also holds docker-compose variables
    )

    # --- General ---------------------------------------------------------
    PROJECT_NAME: str = "Sports Ecosystem & AI Platform"
    VERSION: str = "0.2.0"
    ENVIRONMENT: str = "development"  # development | test | staging | production
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"  # comma separated

    # --- Database (same variables as docker-compose.yml) -------------------
    POSTGRES_USER: str = "sports_admin"
    POSTGRES_PASSWORD: str = "change_me_in_dotenv"
    POSTGRES_DB: str = "sports_ecosystem"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None  # full SQLAlchemy URL; overrides the POSTGRES_* parts
    SQL_ECHO: bool = False

    # --- Security (SRS NFR-SEC-02/03) ---------------------------------------
    SECRET_KEY: str = DEV_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    BCRYPT_ROUNDS: int = 12

    # --- CourtBook (SRS FR-CB-06, FR-CB-10) ---------------------------------
    # `bookings.booking_date` / `time_slot` are WALL-CLOCK values in this zone ("18:00 at the
    # court"), not UTC. Needs the `tzdata` package on platforms without a system zoneinfo.
    VENUE_TIMEZONE: str = "Asia/Ho_Chi_Minh"
    BOOKING_CANCEL_CUTOFF_HOURS: int = 4  # players cannot cancel later than this before the slot
    BOOKING_MAX_ADVANCE_DAYS: int = 90  # how far ahead a slot may be booked

    @property
    def sqlalchemy_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+psycopg2://{user}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _reject_weak_secret_outside_dev(self) -> "Settings":
        if self.ENVIRONMENT.lower() in {"staging", "production", "prod"}:
            weak = (
                self.SECRET_KEY == DEV_SECRET_KEY
                or self.SECRET_KEY.startswith("change_me")
                or len(self.SECRET_KEY) < 32
            )
            if weak:
                raise ValueError("SECRET_KEY must be a random value of >= 32 characters")
        return self


settings = Settings()
