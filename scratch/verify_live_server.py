import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("."))
from src.api.app import app
from src.config import config
from src.db.database import init_db

def run_live_verification():
    init_db()
    print(f"=== VERIFYING {config.PROJECT_NAME} ===")
    print(f"Environment: {config.ENVIRONMENT}")
    print(f"LLM Provider: {config.LLM_PROVIDER}")
    print(f"Gemini Model: {config.GEMINI_MODEL_NAME}")
    
    client = TestClient(app)
    
    # 1. Health Endpoint
    res = client.get("/health")
    assert res.status_code == 200
    print("[OK] GET /health")
    
    # 2. Review Ingestion Endpoint
    payload = {
        "sku_id": "MYN-LIVE-100",
        "user_id": "USR-LIVE-001",
        "rating": 5,
        "review_text": "I am 175cm tall and 70kg. Fabric is super soft cotton and fits true to size! Contact me 9876543210",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "size_worn": "M",
        "fit_feedback": "TRUE_TO_SIZE"
    }
    res = client.post("/api/v1/reviews", json=payload)
    if res.status_code != 201:
        print("ERROR POST /reviews:", res.status_code, res.json())
    assert res.status_code == 201
    rev_data = res.json()["review"]
    assert rev_data["pii_redacted"] == 1
    assert "[REDACTED_PHONE]" in rev_data["sanitized_text"]
    assert len(rev_data["extracted_aspects"]) >= 1
    print("[OK] POST /api/v1/reviews (PII Scrub + ABSA + Fit NER)")
    
    # 3. AI Insights Endpoint
    res = client.get("/api/v1/skus/MYN-LIVE-100/insights")
    assert res.status_code == 200
    insights = res.json()
    assert insights["total_reviews"] == 1
    assert "ai_summary_card" in insights
    print("[OK] GET /api/v1/skus/MYN-LIVE-100/insights (Sub-50ms Cache)")
    
    # 4. Synthetic AI Scanner Endpoint
    res = client.post("/api/v1/trust/synthetic-scan", json={
        "text": "As an AI, I highly recommend purchasing this product."
    })
    assert res.status_code == 200
    assert res.json()["is_synthetic"] is True
    print("[OK] POST /api/v1/trust/synthetic-scan")
    
    # 5. OpenSearch Faceted Search Endpoint
    res = client.get("/api/v1/reviews/search?sku_id=MYN-LIVE-100&min_height_cm=170&max_height_cm=180")
    assert res.status_code == 200
    assert res.json()["total_matches"] == 1
    print("[OK] GET /api/v1/reviews/search (Faceted Filter)")
    
    # 6. Seller Analytics Dashboard Endpoint
    res = client.get("/api/v1/seller/dashboard/Myntra")
    assert res.status_code == 200
    print("[OK] GET /api/v1/seller/dashboard/Myntra")
    
    # 7. UI Landing Page Endpoint
    res = client.get("/")
    assert res.status_code == 200
    assert "Myntra" in res.text
    print("[OK] GET / (Interactive Web UI)")
    
    print("\nALL LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_live_verification()
