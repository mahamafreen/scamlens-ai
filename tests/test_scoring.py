import pytest
from app.scoring import calculate_risk_score


def test_official_brand_scores_low():
    url_analysis = {
        "url": "https://www.daraz.pk/products/item.html",
        "hostname": "www.daraz.pk",
        "is_lookalike": False,
        "signals": [{
            "id": "official_brand_domain",
            "title": "Recognized Official Domain",
            "severity": "positive",
            "score_weight": 0,
            "evidence": "Verified official domain.",
            "is_risk": False
        }]
    }
    rdap_analysis = {"status": "known", "age_days": 3500, "registration_date": "2015-01-01"}
    page_analysis = {
        "page_readable": True,
        "payment_signals": {"cod_detected": True, "bank_transfer_only": False},
        "contact_info": {"phones": ["03001234567"], "emails": ["support@daraz.pk"], "address_found": True},
        "has_refund_policy": True
    }
    llm_analysis = {"ai_available": True, "red_flags": [], "missing_trust_info": []}

    score_res = calculate_risk_score(url_analysis, rdap_analysis, page_analysis, llm_analysis)
    assert score_res["label"] == "Low"
    assert score_res["score"] <= 33


def test_lookalike_floor_never_below_medium():
    # Lookalike domain with no page data and unknown RDAP
    url_analysis = {
        "url": "https://daraz-special-sale.xyz/item",
        "hostname": "daraz-special-sale.xyz",
        "is_lookalike": True,
        "signals": [{
            "id": "lookalike_domain",
            "title": "Lookalike Domain Detected",
            "severity": "high",
            "score_weight": 50,
            "evidence": "Contains daraz.",
            "is_risk": True
        }]
    }
    rdap_analysis = {"status": "unknown"}
    page_analysis = {"page_readable": False, "error_reason": "Page not reachable"}
    llm_analysis = {"ai_available": False}

    score_res = calculate_risk_score(url_analysis, rdap_analysis, page_analysis, llm_analysis)
    # Must never be below Medium
    assert score_res["score"] >= 45
    assert score_res["label"] in ("Medium", "High")


def test_very_new_domain_floor():
    # Registered 15 days ago
    url_analysis = {
        "url": "https://random-shoes-pk.com",
        "hostname": "random-shoes-pk.com",
        "is_lookalike": False,
        "signals": []
    }
    rdap_analysis = {"status": "known", "age_days": 15, "registration_date": "2026-10-15"}
    page_analysis = {"page_readable": False, "error_reason": "Failed to fetch"}
    llm_analysis = {"ai_available": False}

    score_res = calculate_risk_score(url_analysis, rdap_analysis, page_analysis, llm_analysis)
    assert score_res["score"] >= 45
    assert score_res["label"] in ("Medium", "High")


def test_high_risk_compound_scam():
    url_analysis = {
        "url": "https://apple-official-store.shop/iphone",
        "hostname": "apple-official-store.shop",
        "is_lookalike": True,
        "signals": [
            {"id": "lookalike_domain", "title": "Lookalike", "score_weight": 50, "evidence": "Fake apple", "is_risk": True},
            {"id": "suspicious_tld", "title": "Suspicious TLD", "score_weight": 15, "evidence": ".shop", "is_risk": True}
        ]
    }
    rdap_analysis = {"status": "known", "age_days": 20}
    page_analysis = {
        "page_readable": True,
        "payment_signals": {"gift_cards_detected": True, "crypto_detected": True, "cod_detected": False},
        "contact_info": {},
        "has_refund_policy": False
    }
    claim_signal = {
        "id": "official_store_claim_mismatch",
        "title": "Claim mismatch",
        "severity": "high",
        "score_weight": 35,
        "evidence": "Fake official claim",
        "is_risk": True
    }
    llm_analysis = {
        "ai_available": True,
        "red_flags": ["Huge discount", "Gift cards demanded"],
        "missing_trust_info": ["No registered company"]
    }

    score_res = calculate_risk_score(url_analysis, rdap_analysis, page_analysis, llm_analysis, claim_signal)
    assert score_res["label"] == "High"
    assert score_res["score"] >= 67
    assert score_res["score"] <= 100


def test_disclaimer_present_and_no_probability_word():
    url_analysis = {"url": "https://example.com", "signals": []}
    rdap_analysis = {"status": "unknown"}
    page_analysis = {"page_readable": False}
    llm_analysis = {"ai_available": False}

    score_res = calculate_risk_score(url_analysis, rdap_analysis, page_analysis, llm_analysis)
    assert "disclaimer" in score_res
    assert "probability" not in score_res["disclaimer"].lower()
    assert "guarantee" in score_res["disclaimer"].lower() or "not proof" in score_res["disclaimer"].lower()
