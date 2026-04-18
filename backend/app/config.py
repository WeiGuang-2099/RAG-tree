from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Graph RAG Code Analyzer"
    version: str = "0.1.0"
    database_url: str = "sqlite:///./data/code_analysis.db"
    zhipuai_api_key: str = ""
    max_files: int = 500
    max_file_size_mb: int = 5
    supported_extensions: list[str] = [
        ".py", ".js", ".ts", ".tsx", ".jsx", ".vue"
    ]
    ai_timeout: int = 60
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    ws_heartbeat_interval: int = 30
    embedding_cache_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
