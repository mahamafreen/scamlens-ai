import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.rdap_client import check_domain_age_rdap
from app.page_fetcher import fetch_and_parse_page


@pytest.mark.anyio
async def test_rdap_known_domain():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "events": [
            {"eventAction": "registration", "eventDate": "2020-05-10T00:00:00Z"}
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await check_domain_age_rdap("example.com")
        assert res["status"] == "known"
        assert res["age_days"] is not None
        assert res["age_days"] > 1000
        assert res["registration_date"] == "2020-05-10"


@pytest.mark.anyio
async def test_rdap_recent_domain():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "events": [
            {"eventAction": "registration", "eventDate": "2026-10-01T00:00:00Z"}
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await check_domain_age_rdap("newly-created-store.xyz")
        assert res["status"] == "known"
        assert res["age_days"] is not None
        assert res["age_days"] <= 90


@pytest.mark.anyio
async def test_rdap_not_found():
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await check_domain_age_rdap("unknown-tld.pk")
        assert res["status"] == "unknown"
        assert res["age_days"] is None


@pytest.mark.anyio
async def test_page_fetch_and_parse_success():
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Sony WH-1000XM5 Wireless Headphones</title>
        <meta property="og:title" content="Sony WH-1000XM5 Wireless Noise Cancelling Headphones" />
        <meta name="description" content="Buy authentic Sony noise cancelling headphones in Pakistan." />
      </head>
      <body>
        <h1>Sony WH-1000XM5</h1>
        <p>Price: Rs. 84,999</p>
        <p>Contact our support team at info@authenticsound.pk or call +923001234567.</p>
        <p>Our head office is located at Main Boulevard, Gulberg, Lahore.</p>
        <p>We offer full Cash on Delivery across Pakistan.</p>
        <a href="/pages/return-policy">View our 7-day Return Policy</a>
        <a href="/pages/about-us">About Us</a>
      </body>
    </html>
    """

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/html; charset=utf-8"}
    mock_resp.text = sample_html
    mock_resp.content = sample_html.encode("utf-8")
    mock_resp.url = "https://authenticsound.pk/products/sony-wh1000xm5"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        parsed = await fetch_and_parse_page("https://authenticsound.pk/products/sony-wh1000xm5")

        assert parsed["page_readable"] is True
        assert "Sony WH-1000XM5" in parsed["title"]
        assert "84,999" in str(parsed["price_strings"])
        assert "info@authenticsound.pk" in parsed["contact_info"]["emails"]
        assert parsed["contact_info"]["address_found"] is True
        assert parsed["has_refund_policy"] is True
        assert parsed["has_about_page"] is True
        assert parsed["payment_signals"]["cod_detected"] is True
        assert parsed["payment_signals"]["bank_transfer_only"] is False


@pytest.mark.anyio
async def test_page_fetch_suspicious_payment():
    sample_html = """
    <html>
      <head><title>Cheap iPhones</title></head>
      <body>
        <h1>iPhone 15 Pro Max - 70% Off</h1>
        <p>Only Rs. 45,000</p>
        <p>Direct bank transfer only required before shipping. We also accept Bitcoin or USDT. No COD.</p>
      </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.text = sample_html
    mock_resp.content = sample_html.encode("utf-8")
    mock_resp.url = "https://supercheapiphones.top/item"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        parsed = await fetch_and_parse_page("https://supercheapiphones.top/item")

        assert parsed["page_readable"] is True
        assert parsed["payment_signals"]["bank_transfer_only"] is True
        assert parsed["payment_signals"]["crypto_detected"] is True
        assert parsed["payment_signals"]["cod_detected"] is False
        assert parsed["has_refund_policy"] is False


@pytest.mark.anyio
async def test_page_fetch_js_rendered_fallback():
    sample_html = "<html><body><noscript>You need to enable JavaScript to run this app.</noscript><div id='root'></div></body></html>"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.text = sample_html
    mock_resp.content = sample_html.encode("utf-8")
    mock_resp.url = "https://react-app-shop.com"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        parsed = await fetch_and_parse_page("https://react-app-shop.com")

        assert parsed["page_readable"] is False
        assert "JavaScript" in parsed["error_reason"]

