def test_generate_returns_structured_output(client, sample_payload):
    response = client.post("/api/generate", json=sample_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == sample_payload["title"]
    assert body["positive_test_cases"][0]["type"] == "positive"
    assert body["negative_test_cases"][0]["type"] == "negative"
    assert body["edge_cases"][0]["type"] == "edge"
    assert body["api_test_scenarios"][0]["type"] == "api"
    assert body["bug_report_draft"]["severity"] == "High"
    assert len(body["qa_checklist"]) >= 8


def test_missing_required_fields_return_validation_error(client):
    response = client.post("/api/generate", json={"title": "Missing fields"})

    assert response.status_code == 422


def test_history_endpoint_returns_saved_generations(client, sample_payload):
    client.post("/api/generate", json=sample_payload)

    response = client.get("/api/generations")

    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["title"] == sample_payload["title"]
    assert history[0]["positive_count"] == 3


def test_history_endpoint_returns_newest_generation_first(client, sample_payload):
    older_payload = {**sample_payload, "title": "Older checkout scenario"}
    newer_payload = {**sample_payload, "title": "Newer checkout scenario"}
    client.post("/api/generate", json=older_payload)
    client.post("/api/generate", json=newer_payload)

    response = client.get("/api/generations")

    assert response.status_code == 200
    history = response.json()
    assert [item["title"] for item in history] == [
        "Newer checkout scenario",
        "Older checkout scenario",
    ]


def test_generation_detail_returns_one_generation(client, sample_payload):
    created = client.post("/api/generate", json=sample_payload).json()

    response = client.get(f"/api/generations/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_generation_detail_returns_404_for_unknown_id(client):
    response = client.get("/api/generations/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Generation not found"


def test_export_endpoint_returns_markdown(client, sample_payload):
    created = client.post("/api/generate", json=sample_payload).json()

    response = client.get(f"/api/generations/{created['id']}/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "attachment;" in response.headers["content-disposition"]
    assert "# Checkout discount validation" in response.text
    assert "## Positive Test Cases" in response.text
    assert "## Negative Test Cases" in response.text
    assert "## Edge Cases" in response.text
    assert "## API Test Scenarios" in response.text
    assert "## Bug Report Draft" in response.text
    assert "## Retrieved Context" in response.text
    assert "## Model Metadata" in response.text
    assert "## Guardrail Result" in response.text
    assert "- [ ] Confirm the main Checkout happy path" in response.text


def test_export_endpoint_returns_404_for_unknown_id(client):
    response = client.get("/api/generations/999/export")

    assert response.status_code == 404
    assert response.json()["detail"] == "Generation not found"
