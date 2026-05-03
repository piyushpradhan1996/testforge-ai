from app.main import get_ai_provider
from app.services.mock_ai_provider import MockAIProvider


def test_provider_selection_defaults_to_mock(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = get_ai_provider()

    assert isinstance(provider, MockAIProvider)


def test_openai_config_without_key_falls_back_to_mock_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = get_ai_provider()

    assert isinstance(provider, MockAIProvider)


def test_unknown_provider_name_uses_mock_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "unsupported")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = get_ai_provider()

    assert isinstance(provider, MockAIProvider)
