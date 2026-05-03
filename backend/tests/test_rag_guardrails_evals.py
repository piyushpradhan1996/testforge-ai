from app.schemas import GenerateRequest
from app.services.guardrail_service import GuardrailService
from app.services.mock_llm_provider import MockLLMProvider


def test_document_indexing_endpoint_works(client):
    response = client.post(
        "/api/documents",
        json={
            "title": "Checkout API Context",
            "content": "Discount service supports POST /api/checkout/discount. Expired codes return 400 with code EXPIRED_DISCOUNT.",
            "filename": "checkout.md",
            "source_type": "markdown",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Checkout API Context"
    assert body["chunk_count"] >= 1

    list_response = client.get("/api/documents")
    assert list_response.status_code == 200
    assert list_response.json()[0]["title"] == "Checkout API Context"


def test_generation_uses_retrieved_context(client, sample_payload):
    client.post(
        "/api/documents",
        json={
            "title": "Checkout Discount Rules",
            "content": "Checkout discount validation uses POST /api/checkout/discount and rejects expired codes before payment.",
        },
    )

    response = client.post("/api/generate", json=sample_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["model_metadata"]["used_rag"] is True
    assert body["model_metadata"]["retrieved_context_count"] >= 1
    assert body["retrieved_context"][0]["document_title"] == "Checkout Discount Rules"


def test_guardrail_detects_duplicate_test_case_titles(sample_payload):
    request = GenerateRequest(**sample_payload)
    output = MockLLMProvider().generate(request)
    output.negative_test_cases[0].title = output.positive_test_cases[0].title

    result = GuardrailService().validate(output, request=request)

    assert result.warnings
    assert "Duplicate test case titles" in result.warnings[0]


def test_guardrail_detects_missing_required_sections():
    result = GuardrailService().validate({"positive_test_cases": []})

    assert result.passed is False
    assert "Missing required section: negative_test_cases" in result.errors


def test_eval_runner_returns_coverage_scores(client):
    response = client.post("/api/evals/run", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert len(body["results"]) == 4
    assert all(result["schema_valid"] for result in body["results"])
    assert all(result["coverage_score"] >= 80 for result in body["results"])
