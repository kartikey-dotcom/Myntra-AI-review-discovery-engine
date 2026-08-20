import pytest
import os
from fastapi.testclient import TestClient
from src.config import config

config.DB_PATH = "test_myntra_reviews.db"

from src.api.app import app
from src.db.database import init_db, insert_user
from src.services.pii_scrubber import PIIScrubber, LanguageDetector

@pytest.fixture(autouse=True)
def setup_test_db():
    config.DB_PATH = "test_myntra_reviews.db"
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)
    init_db()
    insert_user("USR-202", "verified_denim_buyer", account_age_days=100, is_verified=1)
    yield
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)

client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. PII Scrubbing & Language Detection Tests
# -----------------------------------------------------------------------------

def test_pii_redaction_phone_numbers():
    text = "Great t-shirt! Call me at 9876543210 or 9 8 7 6 5 4 3 2 1 0 for size swap."
    sanitized, is_redacted = PIIScrubber.sanitize(text)
    assert is_redacted is True
    assert "9876543210" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized

def test_pii_redaction_email_and_urls():
    text = "Check photos at http://myphotos.com or contact user@gmail.com for details."
    sanitized, is_redacted = PIIScrubber.sanitize(text)
    assert is_redacted is True
    assert "[REDACTED_URL]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized

def test_pii_redaction_social_handles():
    text = "Follow my fashion page @fashion_guy or Ig: @style_guru"
    sanitized, is_redacted = PIIScrubber.sanitize(text)
    assert is_redacted is True
    assert "[REDACTED_HANDLE]" in sanitized

def test_language_detection():
    assert LanguageDetector.detect("This is a great product with soft fabric") == "en"
    assert LanguageDetector.detect("Fabric bohot accha hai but fitting ekdam bakwas hai") == "hinglish"
    assert LanguageDetector.detect("यह बहुत अच्छा टी-शर्ट है") == "hi"

# -----------------------------------------------------------------------------
# 2. Out-of-Bound Height & Weight Validation Tests
# -----------------------------------------------------------------------------

def test_invalid_height_boundary():
    payload = {
        "sku_id": "MYN-TSHIRT-101",
        "user_id": "USR-101",
        "rating": 5,
        "review_text": "Great fit!",
        "height_cm": 300.0  # Invalid height (> 220cm boundary)
    }
    response = client.post("/api/v1/reviews", json=payload)
    assert response.status_code == 422  # Validation Error

def test_invalid_weight_boundary():
    payload = {
        "sku_id": "MYN-TSHIRT-101",
        "user_id": "USR-101",
        "rating": 5,
        "review_text": "Nice material!",
        "weight_kg": 15.0  # Invalid weight (< 30kg boundary)
    }
    response = client.post("/api/v1/reviews", json=payload)
    assert response.status_code == 422

# -----------------------------------------------------------------------------
# 3. End-to-End Review Ingestion & Summary API Tests
# -----------------------------------------------------------------------------

def test_successful_review_submission_and_summary():
    insert_user("USR-202", "verified_denim_buyer", account_age_days=100, is_verified=1)
    payload = {
        "sku_id": "MYN-JEANS-999",
        "user_id": "USR-202",
        "rating": 5,
        "review_text": "Superb stretch denim! Call me 9876543210 for pics",
        "height_cm": 178.0,
        "weight_kg": 72.0,
        "size_worn": "32",
        "fit_feedback": "TRUE_TO_SIZE"
    }
    response = client.post("/api/v1/reviews", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["review"]["pii_redacted"] == 1
    assert "[REDACTED_PHONE]" in data["review"]["sanitized_text"]
    
    # Verify SKU Summary API
    summary_resp = client.get("/api/v1/skus/MYN-JEANS-999/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert summary_data["total_reviews"] == 1
    assert summary_data["avg_rating"] == 5.0
    assert summary_data["fit_summary"]["true_to_size_pct"] == 100.0

def test_rating_sentiment_variance_moderation_queue():
    payload = {
        "sku_id": "MYN-JACKET-909",
        "user_id": "USR-303",
        "rating": 5,
        "review_text": "This jacket is terrible and a waste of money, zipper broke on day 1",
        "fit_feedback": "RUNS_SMALL"
    }
    response = client.post("/api/v1/reviews", json=payload)
    assert response.status_code == 201
    review_data = response.json()["review"]
    assert review_data["moderation_status"] == "PENDING"
    
    # Check Moderation Queue API
    mod_resp = client.get("/api/v1/moderation/queue")
    assert mod_resp.status_code == 200
    mod_data = mod_resp.json()
    assert mod_data["open_count"] >= 1
    
    # Perform Ops Decision to Approve
    decide_payload = {
        "review_id": review_data["review_id"],
        "decision": "APPROVED",
        "reason": "Verified purchase after user clarified rating"
    }
    decide_resp = client.post("/api/v1/moderation/decide", json=decide_payload)
    assert decide_resp.status_code == 200
    assert decide_resp.json()["new_status"] == "APPROVED"
