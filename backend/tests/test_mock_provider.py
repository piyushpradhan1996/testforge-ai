from app.schemas import GenerateRequest
from app.services.mock_ai_provider import MockAIProvider


def test_mock_provider_returns_deterministic_sections():
    request = GenerateRequest(
        title="Profile email update",
        requirement="Users can update their profile email after entering a valid verification code.",
        acceptance_criteria="Email is changed only after verification. Old email receives a notification.",
        api_notes="PATCH /api/profile/email",
        feature_area="Profile",
        priority="Medium",
    )
    provider = MockAIProvider()

    first = provider.generate(request)
    second = provider.generate(request)

    assert first.model_dump() == second.model_dump()
    assert first.positive_test_cases[0].title == "Verify successful Profile email update flow with valid inputs"
    assert first.negative_test_cases[0].type == "negative"
    assert first.api_test_scenarios[0].preconditions[0] == "API notes: PATCH /api/profile/email"
    assert "Old email receives a notification" in first.qa_checklist[-1]
    assert first.model_metadata.provider == "mock"
    assert first.model_metadata.prompt_version == "qa_generation_v1"
    assert first.model_metadata.used_rag is False
