import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TESTFORGE_DB_PATH", str(tmp_path / "testforge-test.db"))
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def sample_payload():
    return {
        "title": "Checkout discount validation",
        "requirement": "As a shopper, I want to apply a valid discount code during checkout so that my order total is reduced.",
        "acceptance_criteria": "Valid discount codes reduce the order total. Expired codes show an error. Discount totals are visible before payment.",
        "api_notes": "POST /api/checkout/discount with code and cartId. Returns adjustedTotal and discountAmount.",
        "feature_area": "Checkout",
        "priority": "High",
    }

