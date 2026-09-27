from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class GeoSeisSettings(BaseSettings):
    """General Settings for the Geoseis Project.

    Args:
        BaseSettings (_type_): Inherit Pydantic BaseSettings Class for environment variable management.
    """

    model_config = SettingsConfigDict(
        env_prefix="GEOSEIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
    RAW_DATA_DIR: Path = PROJECT_ROOT / "data" / "raw"
    RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
