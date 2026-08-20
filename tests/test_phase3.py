import pytest
import os
from fastapi.testclient import TestClient
from src.config import config

config.DB_PATH = "test_phase3_myntra_reviews.db"

from src.api.app import app
from src.db.database import init_db, insert_user, insert_sku
from src.services.absa_engine import ABSAEngine
from src.services.fit_intelligence import FitIntelligenceEngine
from src.services.summarizer import LLMClusterSummarizer
from src.services.cv_filter import ComputerVisionFilter

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists(config.DB_PATH):
        try:
            os.remove(config.DB_PATH)
        except Exception:
            pass
    init_db()
    insert_user("BUYER-PHASE3-001", "stylish_buyer", account_age_days=60, is_verified=1)
    insert_sku("SKU-PHASE3-100", "Premium Linen Shirt", "Myntra Select", "Shirts")
    yield
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)

client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. ABSA Engine Unit Tests
# -----------------------------------------------------------------------------

def test_absa_fabric_and_color_extraction():
    text = "The fabric is super soft and breathable, but the color is dull compared to photo."
    aspects = ABSAEngine.extract_aspects(text)
    assert len(aspects) >= 2
    
    aspect_names = [a["aspect"] for a in aspects]
    assert "Fabric Quality" in aspect_names
    assert "Color Accuracy" in aspect_names
    
    fabric_asp = next(a for a in aspects if a["aspect"] == "Fabric Quality")
    assert fabric_asp["polarity"] == "POSITIVE"
    
    color_asp = next(a for a in aspects if a["aspect"] == "Color Accuracy")
    assert color_asp["polarity"] == "NEGATIVE"

# -----------------------------------------------------------------------------
# 2. Fit Intelligence & Body Metric NER Tests
# -----------------------------------------------------------------------------

def test_fit_intelligence_feet_inches_conversion():
    text = "I am 5'9 ft and weight 70 kg, broad shoulders, fits tight on chest so order size up."
    metrics = FitIntelligenceEngine.extract_body_metrics(text)
    assert metrics["extracted_height_cm"] == 175.3
    assert metrics["extracted_weight_kg"] == 70.0
    assert metrics["extracted_body_build"] == "HEAVY"  # Matched broad
    
    fit_delta = FitIntelligenceEngine.classify_fit_delta(text)
    assert fit_delta == "RUNS_SMALL"

def test_fit_intelligence_cm_and_lbs():
    text = "Height 180cm, weight 150 lbs, athletic build, perfect fit!"
    metrics = FitIntelligenceEngine.extract_body_metrics(text)
    assert metrics["extracted_height_cm"] == 180.0
    assert metrics["extracted_weight_kg"] == 68.0
    assert metrics["extracted_body_build"] == "ATHLETIC"
    
    fit_delta = FitIntelligenceEngine.classify_fit_delta(text)
    assert fit_delta == "TRUE_TO_SIZE"

# -----------------------------------------------------------------------------
# 3. LLM Cluster Summarizer Tests
# -----------------------------------------------------------------------------

def test_summarizer_pros_cons_generation():
    reviews = [{"review_id": "r1"}, {"review_id": "r2"}]
    aspects = [
        {"aspect": "Fabric Quality", "polarity": "POSITIVE"},
        {"aspect": "Fabric Quality", "polarity": "POSITIVE"},
        {"aspect": "Shrinkage & Wash Care", "polarity": "NEGATIVE"}
    ]
    summary = LLMClusterSummarizer.generate_sku_summary(reviews, aspects)
    assert "pros" in summary
    assert "cons" in summary
    assert len(summary["pros"]) >= 1

# -----------------------------------------------------------------------------
# 4. Computer Vision Quality Filter Tests
# -----------------------------------------------------------------------------

def test_cv_filter_valid_photo():
    dummy_bytes = b"x" * (100 * 1024)
    accepted, reason, metrics = ComputerVisionFilter.evaluate_image_metadata(dummy_bytes, "garment_fit.jpg")
    assert accepted is True

def test_cv_filter_unsupported_format():
    dummy_bytes = b"x" * (100 * 1024)
    accepted, reason, metrics = ComputerVisionFilter.evaluate_image_metadata(dummy_bytes, "garment.pdf")
    assert accepted is False
    assert "Unsupported image format" in reason

# -----------------------------------------------------------------------------
# 5. Phase 3 API Integration Endpoints Tests
# -----------------------------------------------------------------------------

def test_extract_aspects_api_endpoint():
    resp = client.post("/api/v1/reviews/extract-aspects", json={
        "text": "I am 5'10 ft, fabric is super soft cotton, but runs small so size up."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["extracted_aspects"]) >= 1
    assert data["extracted_body_metrics"]["extracted_height_cm"] == 177.8
    assert data["inferred_fit_delta"] == "RUNS_SMALL"

def test_sku_insights_api_endpoint():
    # Ingest a review first
    client.post("/api/v1/reviews", json={
        "sku_id": "SKU-PHASE3-100",
        "user_id": "BUYER-PHASE3-001",
        "rating": 5,
        "review_text": "I am 175cm tall, fabric is soft and comfortable. Perfect fit!",
        "fit_feedback": "TRUE_TO_SIZE"
    })
    
    resp = client.get("/api/v1/skus/SKU-PHASE3-100/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sku_id"] == "SKU-PHASE3-100"
    assert data["total_reviews"] == 1
    assert "ai_summary_card" in data
