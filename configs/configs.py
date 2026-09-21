from pathlib import Path

from pydantic_settings import BaseSettings


class GeoseisSettings(BaseSettings):
    """General Settings for the Geoseis Project.

    Args:
        BaseSettings (_type_): Inherit Pydantic BaseSettings Class for environment variable management.
    """

    PROJECT_ROOT: Path = Path.home() / "Documents" / "GitHub" / "Lady-knox-analysis"
    RAW_DATA_DIR: Path = PROJECT_ROOT / "data" / "raw" / "LK"
    RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"