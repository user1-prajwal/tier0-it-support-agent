import pytest
from app.config import Settings
from pydantic import ValidationError

DB_URL = "postgresql+psycopg://tier0:s3cret-pw@localhost:5432/tier0"


def test_database_url_has_no_default():
    assert Settings.model_fields["database_url"].is_required()


def test_missing_database_url_fails_loudly(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_database_url_is_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", DB_URL)
    settings = Settings(_env_file=None)
    assert settings.database_url.get_secret_value() == DB_URL


def test_database_password_is_not_printed(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", DB_URL)
    settings = Settings(_env_file=None)
    assert "s3cret-pw" not in repr(settings)
    assert "s3cret-pw" not in str(settings)


def test_llm_provider_defaults_to_fake(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", DB_URL)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert Settings(_env_file=None).llm_provider == "fake"


def test_unknown_llm_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", DB_URL)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)