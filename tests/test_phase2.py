import pytest
import os
from fastapi.testclient import TestClient
from src.config import config

config.DB_PATH = "test_phase2_myntra_reviews.db"

from src.api.app import app
from src.db.database import init_db, insert_user, insert_sku
from src.services.synthetic_detector import SyntheticTextDetector
from src.services.behavioral_profiler import BehavioralProfiler
from src.services.moderation_rules import ModerationRuleEngine

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)
    init_db()
    
    # Pre-seed verified user and unverified new user
    insert_user("VERIFIED-USER-100", "verified_buyer", account_age_days=180, is_verified=1)
    insert_user("NEW-BOT-USER-999", "spam_bot", account_age_days=1, is_verified=0)
    insert_sku("SKU-TEST-001", "Test T-Shirt", "BrandX", "Apparel")
    
    yield
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)

client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. Synthetic Text Detector Unit Tests
# -----------------------------------------------------------------------------

def test_synthetic_detector_human_text():
    human_text = "Shirt fabric is soft. Fit is a bit tight on shoulders though."
    is_synth, score, metrics = SyntheticTextDetector.analyze(human_text)
    assert is_synth is False
    assert score < 0.50

def test_synthetic_detector_bot_template_text():
    bot_text = "As an AI, I highly recommend purchasing this product. Top notch quality product that exceeded my expectations in every way. In conclusion, must buy product."
    is_synth, score, metrics = SyntheticTextDetector.analyze(bot_text)
    assert is_synth is True
    assert score >= 0.70
    assert metrics["template_matches"] >= 2

# -----------------------------------------------------------------------------
# 2. Behavioral Profiler Unit Tests
# -----------------------------------------------------------------------------

def test_behavioral_profiler_verified_purchaser():
    profile = BehavioralProfiler.evaluate_user_trust("VERIFIED-USER-100", "SKU-TEST-001")
    assert profile["is_verified_purchaser"] is True
    assert profile["trust_score"] == 1.0
    assert profile["risk_score"] == 0.0

def test_behavioral_profiler_unverified_new_account():
    profile = BehavioralProfiler.evaluate_user_trust("NEW-BOT-USER-999", "SKU-TEST-001")
    assert profile["is_verified_purchaser"] is False
    assert profile["risk_score"] >= 0.60
    assert "Unverified Purchaser" in profile["risk_reasons"]

# -----------------------------------------------------------------------------
# 3. Moderation Rule Engine & Pipeline Integration Tests
# -----------------------------------------------------------------------------

def test_fast_track_auto_approval_for_verified_buyer():
    payload = {
        "sku_id": "SKU-TEST-001",
        "user_id": "VERIFIED-USER-100",
        "rating": 5,
        "review_text": "Fits nicely! Fabric quality is good and stitching is durable.",
        "fit_feedback": "TRUE_TO_SIZE"
    }
    status, synth_score, reason, metrics = ModerationRuleEngine.evaluate(payload)
    assert status == "APPROVED"
    assert "Fast-track approval" in reason

def test_escalation_for_unverified_bot_review():
    payload = {
        "sku_id": "SKU-TEST-001",
        "user_id": "NEW-BOT-USER-999",
        "rating": 5,
        "review_text": "As an AI, I highly recommend purchasing this top notch quality product.",
        "fit_feedback": "RUNS_LARGE"
    }
    status, synth_score, reason, metrics = ModerationRuleEngine.evaluate(payload)
    assert status in ("PENDING", "REJECTED")

# -----------------------------------------------------------------------------
# 4. Phase 2 End-to-End API Tests
# -----------------------------------------------------------------------------

def test_synthetic_scan_api_endpoint():
    resp = client.post("/api/v1/trust/synthetic-scan", json={
        "text": "As an AI, I highly recommend purchasing this top notch quality product."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_synthetic"] is True
    assert data["synthetic_confidence_score"] >= 0.70

def test_moderation_stats_api_endpoint():
    # Submit 1 verified review (Auto-Approved)
    client.post("/api/v1/reviews", json={
        "sku_id": "SKU-TEST-001",
        "user_id": "VERIFIED-USER-100",
        "rating": 4,
        "review_text": "Good fabric and fast delivery.",
        "fit_feedback": "TRUE_TO_SIZE"
    })
    
    # Submit 1 synthetic bot review (Flagged)
    client.post("/api/v1/reviews", json={
        "sku_id": "SKU-TEST-001",
        "user_id": "NEW-BOT-USER-999",
        "rating": 5,
        "review_text": "As an AI, I highly recommend purchasing this top notch quality product.",
        "fit_feedback": "RUNS_LARGE"
    })
    
    stats_resp = client.get("/api/v1/moderation/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_reviews_ingested"] == 2
    assert stats["approved_count"] == 1
    assert stats["synthetic_ai_flagged_count"] >= 1
