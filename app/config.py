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
    
    rerank_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    
    # Only the seed script needs this. No default: a password must be chosen on purpose.
    demo_password: SecretStr | None = None
    
    # Signing key for access tokens. Checked at startup and before every use. See auth/tokens.py.
    jwt_secret: SecretStr | None = None
    access_token_minutes: int = 60
    login_max_failures: int = 5
    login_window_seconds: int = 300