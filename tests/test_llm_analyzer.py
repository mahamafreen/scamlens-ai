import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.llm_analyzer import (
    clean_think_blocks,
    extract_json_from_llm,
    analyze_with_llm,
    check_official_store_claim_mismatch
)


def test_clean_think_blocks():
    text_with_think = "<think>Let me analyze this shop. It seems fake.</think>{\"product_name\": \"iPhone 15\"}"
    cleaned = clean_think_blocks(text_with_think)
    assert cleaned == "{\"product_name\": \"iPhone 15\"}"

    # Unclosed think tag
    cut_off = "<think>Still reasoning about the page"
    assert clean_think_blocks(cut_off) == ""


def test_extract_json_from_llm():
    # Direct JSON
    valid = "{\"product_name\": \"Shoe\", \"claims_official_store\": false}"
    res = extract_json_from_llm(valid)
    assert res is not None
    assert res["product_name"] == "Shoe"

    # Markdown fence
    fenced = "```json\n{\"product_name\": \"Watch\", \"brand_claimed\": \"Rolex\"}\n```"
    res_fenced = extract_json_from_llm(fenced)
    assert res_fenced is not None
    assert res_fenced["brand_claimed"] == "Rolex"

    # With think tags
    with_think = "<think>thinking here...</think>\n```json\n{\"product_name\": \"Headphones\"}\n```"
    res_think = extract_json_from_llm(with_think)
    assert res_think is not None
    assert res_think["product_name"] == "Headphones"

    # Malformed
    assert extract_json_from_llm("Not a json string at all") is None


@pytest.mark.anyio
async def test_analyze_with_llm_success():
    mock_choice = MagicMock()
    mock_choice.message.content = """<think>Analysis done</think>
    {
      "product_name": "AirPods Pro 2",
      "brand_claimed": "Apple",
      "price_text": "Rs. 9,999",
      "claims_official_store": true,
      "red_flags": ["Price is unrealistically low (authentic is Rs 65k+)", "Urgency countdown timer"],
      "missing_trust_info": ["No registered physical office in Pakistan"],
      "summary": "High risk of counterfeit product. Authentic Apple AirPods cannot be sold for Rs 9,999."
    }"""
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("openai.resources.chat.completions.AsyncCompletions.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        analysis = await analyze_with_llm(
            url="https://airpods-cheap.top",
            hostname="airpods-cheap.top",
            title="AirPods Pro Super Sale",
            visible_text="Official Apple Store clearance. 85% discount."
        )

        assert analysis["ai_available"] is True
        assert analysis["product_name"] == "AirPods Pro 2"
        assert analysis["brand_claimed"] == "Apple"
        assert analysis["claims_official_store"] is True
        assert len(analysis["red_flags"]) >= 1


@pytest.mark.anyio
async def test_analyze_with_llm_model_offline_fallback():
    with patch("openai.resources.chat.completions.AsyncCompletions.create", side_effect=Exception("Connection refused")):
        analysis = await analyze_with_llm(
            url="https://some-shop.com",
            hostname="some-shop.com",
            title="Some Product",
            visible_text="Some text here"
        )
        assert analysis["ai_available"] is False
        assert "unavailable" in analysis["ai_error"].lower() or "connection" in analysis["ai_error"].lower()
        assert analysis["product_name"] == "Some Product"


def test_official_store_claim_mismatch():
    # Apple claimed on fake domain
    sig = check_official_store_claim_mismatch(
        claims_official=True,
        brand_claimed="Apple",
        hostname="apple-sale-store.shop"
    )
    assert sig is not None
    assert sig["id"] == "official_store_claim_mismatch"
    assert "apple" in sig["evidence"].lower()

    # Apple claimed on real domain
    sig_real = check_official_store_claim_mismatch(
        claims_official=True,
        brand_claimed="Apple",
        hostname="apple.com"
    )
    assert sig_real is None

    # Not claiming official store
    sig_false = check_official_store_claim_mismatch(
        claims_official=False,
        brand_claimed="Apple",
        hostname="random-electronics.pk"
    )
    assert sig_false is None
