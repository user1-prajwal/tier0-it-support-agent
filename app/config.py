from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (or a local .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # No default: the app must refuse to start without a database, not guess one.
    database_url: SecretStr

    # "fake" means no external calls, so forgetting to configure is the safe case.
    llm_provider: Literal["groq", "gemini", "ollama", "openrouter", "fake"] = "fake"
    
    # Local embedding model. Downloaded once, then reused offline from the cache folder.
    embed_model: str = "BAAI/bge-small-en-v1.5"
    embed_cache_dir: str = ".cache/fastembed"