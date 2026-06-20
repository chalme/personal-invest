from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Personal Invest"
    app_version: str = "0.1.0"
    root_dir: Path = Path(__file__).resolve().parents[3]
    storage_dir: Path = root_dir / "storage"
    sqlite_path: Path = storage_dir / "invest.db"
    duckdb_path: Path = storage_dir / "invest.duckdb"
    data_dir: Path = root_dir / "data"
    reports_dir: Path = root_dir / "reports"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    return settings

