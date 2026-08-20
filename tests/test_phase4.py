import pytest
import os
from fastapi.testclient import TestClient
from src.config import config

config.DB_PATH = "test_phase4_myntra_reviews.db"

from src.api.app import app
from src.db.database import init_db, insert_user, insert_sku
from src.services.caching_layer import RedisCacheManager
from src.services.search_index import OpenSearchIndexEngine
from src.services.seller_analytics import SellerAnalyticsEngine

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)
    init_db()
    RedisCacheManager.clear()
    
    insert_user("SELLER-BUYER-001", "roadster_fan", account_age_days=90, is_verified=1)
    insert_sku("MYN-TSHIRT-101", "Roadster Pure Cotton T-Shirt", "Roadster", "Apparel")
    yield
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)

client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. Redis Cache Manager Unit Tests
# -----------------------------------------------------------------------------

def test_redis_cache_hit_and_invalidation():
    sku_id = "MYN-TSHIRT-101"
    mock_summary = {"total_reviews": 50, "avg_rating": 4.6}
    
    # Set Cache
    RedisCacheManager.set_summary(sku_id, mock_summary)
    
    cached = RedisCacheManager.get_summary(sku_id)
    assert cached is not None
    assert cached["_cached"] is True
    assert cached["total_reviews"] == 50
    
    # Invalidate Cache
    RedisCacheManager.invalidate(sku_id)
    assert RedisCacheManager.get_summary(sku_id) is None

# -----------------------------------------------------------------------------
# 2. OpenSearch Faceted Search Tests
# -----------------------------------------------------------------------------

def test_opensearch_faceted_search():
    # Ingest 2 reviews with different metrics
    client.post("/api/v1/reviews", json={
        "sku_id": "MYN-TSHIRT-101",
        "user_id": "SELLER-BUYER-001",
        "rating": 5,
        "review_text": "Great t-shirt for tall guy, very soft cotton!",
        "height_cm": 185.0,
        "weight_kg": 78.0,
        "body_build": "ATHLETIC",
        "size_worn": "L"
    })
    
    # Search for tall height range (180-190cm)
    res = OpenSearchIndexEngine.search_reviews(
        sku_id="MYN-TSHIRT-101",
        min_height_cm=180.0,
        max_height_cm=190.0
    )
    assert res["total_matches"] == 1
    assert res["reviews"][0]["height_cm"] == 185.0

# -----------------------------------------------------------------------------
# 3. Seller Analytics Dashboard Tests
# -----------------------------------------------------------------------------

def test_seller_analytics_dashboard():
    analytics = SellerAnalyticsEngine.get_brand_analytics("Roadster")
    assert analytics["brand"] == "Roadster"
    assert "size_calibration_recommendation" in analytics

# -----------------------------------------------------------------------------
# 4. Phase 4 API Endpoints Tests
# -----------------------------------------------------------------------------

def test_faceted_search_api_endpoint():
    resp = client.get("/api/v1/reviews/search?sku_id=MYN-TSHIRT-101&body_build=ATHLETIC")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_matches" in data

def test_seller_dashboard_api_endpoint():
    resp = client.get("/api/v1/seller/dashboard/Roadster")
    assert resp.status_code == 200
    data = resp.json()
    assert data["brand"] == "Roadster"

def test_root_ui_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Myntra" in resp.text
