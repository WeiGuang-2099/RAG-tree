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
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".vue"
    ]
    ai_timeout: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
