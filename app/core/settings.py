from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -------------------------------------------------------------------------
    # LOGGING
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    log_file: Path = Path.home() / ".melodyengine" / "app.log"
    log_file_max_size: int = 25 * 1024 * 1024
    log_file_backup_count: int = 7
    log_format: str = "%(asctime)s %(levelname)-7s [%(name)s] (%(threadName)s) %(message)s"

    # -------------------------------------------------------------------------
    # HTTP and CORS
    # -------------------------------------------------------------------------
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    cors_origins: list[str] = ["*"]

    # -------------------------------------------------------------------------
    # GENERATION SETTINGS
    # -------------------------------------------------------------------------
    output_dir: Path = Path.home() / ".melodyengine" / "outputs"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
