import pytest
import os
from fastapi.testclient import TestClient
from src.api.app import app
from src.config import config
from src.db.database import init_db
from src.services.absa_engine import ABSAEngine
from src.services.verification_engine import VerificationEngine
from src.services.corpus_analytics import CorpusAnalyticsEngine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists(config.DB_PATH):
        try:
            os.remove(config.DB_PATH)
        except Exception:
            pass
    init_db()

def test_expanded_taxonomy_extraction():
    text = "I kept this dress in my wishlist for 3 weeks because size chart is confusing and fit is tight."
    aspects = ABSAEngine.extract_aspects(text)
    categories = [a["aspect_name"] for a in aspects]
    assert "size_fit_uncertainty" in categories
    assert "wishlist_behavior" in categories

def test_adversarial_verification_pass():
    # Valid Claim & Quote Alignment
    claim = "Shoppers defer purchase due to uncertainty regarding size chart accuracy."
    quote = "size chart is confusing and fit is tight across chest"
    is_valid, reason = VerificationEngine.verify_claim(claim, quote, "size_fit_uncertainty")
    assert is_valid is True

    # Invalid Claim & Short Quote
    short_quote = "good"
    is_valid_short, reason_short = VerificationEngine.verify_claim(claim, short_quote, "size_fit_uncertainty")
    assert is_valid_short is False
    assert "too short" in reason_short

def test_corpus_analytics_api_endpoint():
    res = client.get("/api/v1/corpus/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "total_corpus_reviews" in data
    assert "category_breakdown" in data
    assert "size_fit_uncertainty" in data["category_breakdown"]

def test_verified_findings_api_endpoint():
    res = client.get("/api/v1/corpus/verified-findings")
    assert res.status_code == 200
    data = res.json()
    assert "verified_findings" in data

def test_rejected_log_api_endpoint():
    res = client.get("/api/v1/corpus/rejected-log")
    assert res.status_code == 200
    data = res.json()
    assert "rejected_log" in data

def test_record_click_traceability_api_endpoint():
    # Submit review
    post_res = client.post("/api/v1/reviews", json={
        "sku_id": "SKU-TRACE-001",
        "user_id": "USR-TRACE-100",
        "rating": 4,
        "review_text": "I kept this in my wishlist for weeks because size chart was tight.",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "fit_feedback": "RUNS_SMALL"
    })
    assert post_res.status_code == 201
    rev_id = post_res.json()["review"]["review_id"]

    # Trace record by ID
    rec_res = client.get(f"/api/v1/corpus/records/{rev_id}")
    assert rec_res.status_code == 200
    record = rec_res.json()
    assert record["review_id"] == rev_id
    assert record["sku_id"] == "SKU-TRACE-001"
    assert "[REDACTED" in record["sanitized_text"] or "wishlist" in record["sanitized_text"]
