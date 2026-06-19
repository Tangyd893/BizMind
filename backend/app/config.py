from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(
        default="postgresql+asyncpg://bizmind:bizmind@localhost:5433/bizmind",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="bizmind_chunks", alias="QDRANT_COLLECTION")

    storage_path: str = Field(default="./data/uploads", alias="STORAGE_PATH")
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")

    jwt_expire_hours: int = Field(default=24, alias="JWT_EXPIRE_HOURS")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.deepseek.com/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")

    embedding_api_key: str = Field(default="", alias="EMBEDDING_API_KEY")
    embedding_base_url: str = Field(
        default="https://api.siliconflow.cn/v1", alias="EMBEDDING_BASE_URL"
    )
    embedding_model: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL")
    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    embedding_dim: int = Field(default=1024, alias="EMBEDDING_DIM")
    chunk_size: int = Field(default=512, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=64, alias="CHUNK_OVERLAP")
    parent_chunk_size: int = Field(default=2048, alias="PARENT_CHUNK_SIZE")
    retrieval_top_k: int = Field(default=20, alias="RETRIEVAL_TOP_K")
    rerank_top_k: int = Field(default=4, alias="RERANK_TOP_K")

    grade_threshold: float = Field(default=0.5, alias="GRADE_THRESHOLD")
    max_retrieval_retries: int = Field(default=2, alias="MAX_RETRIEVAL_RETRIES")
    max_critique_retries: int = Field(default=1, alias="MAX_CRITIQUE_RETRIES")
    web_search_enabled: bool = Field(default=False, alias="WEB_SEARCH_ENABLED")

    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="http://localhost:3001", alias="LANGFUSE_HOST")
    langfuse_enabled: bool = Field(default=False, alias="LANGFUSE_ENABLED")

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()
