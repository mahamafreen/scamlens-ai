import pytest
from starlette.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app

client = TestClient(app)


def test_index_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "ScamLens" in response.text


def test_health_route():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ollama_model" in data


def test_api_check_quick_route():
    with patch("app.main.fetch_and_parse_page", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.check_domain_age_rdap", new_callable=AsyncMock) as mock_rdap:
        
        mock_fetch.return_value = {
            "page_readable": True,
            "title": "Nike Air Max",
            "visible_text": "Buy shoes here",
            "payment_signals": {"cod_detected": True},
            "contact_info": {"phones": [], "emails": []},
            "has_refund_policy": True
        }
        mock_rdap.return_value = {"status": "known", "age_days": 500, "details": "Old"}

        response = client.post("/api/check-quick", json={"url": "https://nike.com/shoes"})
        assert response.status_code == 200
        data = response.json()
        assert "score_data" in data
        assert "alternatives" in data
        assert data["hostname"] == "nike.com"


def test_full_check_route_post_json():
    with patch("app.main.fetch_and_parse_page", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.check_domain_age_rdap", new_callable=AsyncMock) as mock_rdap, \
         patch("app.main.analyze_with_llm", new_callable=AsyncMock) as mock_llm:
        
        mock_fetch.return_value = {
            "page_readable": True,
            "title": "Cheap Apple Store",
            "visible_text": "Official Apple Store",
            "payment_signals": {"bank_transfer_only": True, "crypto_detected": True},
            "contact_info": {},
            "has_refund_policy": False
        }
        mock_rdap.return_value = {"status": "known", "age_days": 10, "details": "Recent"}
        mock_llm.return_value = {
            "ai_available": True,
            "claims_official_store": True,
            "brand_claimed": "Apple",
            "product_name": "iPhone 15",
            "red_flags": ["Fake store claim"],
            "missing_trust_info": ["No phone number"],
            "summary": "High risk store"
        }

        response = client.post("/check", json={"url": "https://apple-sale.shop/item"})
        assert response.status_code == 200
        data = response.json()
        assert data["score_data"]["label"] == "High"
        assert data["score_data"]["score"] >= 67
