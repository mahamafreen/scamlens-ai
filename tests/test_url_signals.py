import pytest
from app.url_signals import analyze_url_signals, levenshtein_distance


def test_levenshtein_distance():
    assert levenshtein_distance("daraz", "daraz") == 0
    assert levenshtein_distance("daraz", "daeraz") == 1
    assert levenshtein_distance("apple", "aple") == 1
    assert levenshtein_distance("nike", "bike") == 1


def test_insecure_http_signal():
    res = analyze_url_signals("http://example-store.com/item/1")
    signals = res["signals"]
    ids = [s["id"] for s in signals]
    assert "insecure_http" in ids


def test_ip_address_host():
    res = analyze_url_signals("http://192.168.1.100/checkout")
    signals = res["signals"]
    ids = [s["id"] for s in signals]
    assert "ip_address_host" in ids


def test_punycode_host():
    res = analyze_url_signals("https://xn--pple-43d.com/iphone")
    signals = res["signals"]
    ids = [s["id"] for s in signals]
    assert "punycode_host" in ids


def test_url_shortener():
    res = analyze_url_signals("https://bit.ly/deal123")
    assert res["is_shortener"] is True
    signals = res["signals"]
    ids = [s["id"] for s in signals]
    assert "shortened_url" in ids


def test_suspicious_tld():
    res = analyze_url_signals("https://super-deals.xyz/sale")
    signals = res["signals"]
    ids = [s["id"] for s in signals]
    assert "suspicious_tld" in ids


def test_excessive_hyphens_and_digits():
    res = analyze_url_signals("https://mega-phone-super-deals-sale.com")
    signals = res["signals"]
    ids = [s["id"] for s in signals]
    assert "excessive_hyphens" in ids

    res_digits = analyze_url_signals("https://cheapmarket98234.com")
    ids_digits = [s["id"] for s in res_digits["signals"]]
    assert "excessive_digits" in ids_digits


def test_lookalike_brand_impersonation():
    # Daraz impersonation
    res_daraz = analyze_url_signals("https://daraz-super-deals.com/product")
    assert res_daraz["is_lookalike"] is True
    ids_daraz = [s["id"] for s in res_daraz["signals"]]
    assert "lookalike_domain" in ids_daraz

    # Apple impersonation
    res_apple = analyze_url_signals("https://apple-official-store.shop/iphone")
    assert res_apple["is_lookalike"] is True
    ids_apple = [s["id"] for s in res_apple["signals"]]
    assert "lookalike_domain" in ids_apple


def test_typosquatting_detection():
    # Typo on daraz
    res_typo = analyze_url_signals("https://daeraz.pk/items")
    assert res_typo["is_lookalike"] is True
    ids_typo = [s["id"] for s in res_typo["signals"]]
    assert "typosquat_lookalike" in ids_typo


def test_legitimate_official_brand():
    # Official Daraz
    res_daraz = analyze_url_signals("https://www.daraz.pk/products/test-item.html")
    assert res_daraz["is_lookalike"] is False
    ids_daraz = [s["id"] for s in res_daraz["signals"]]
    assert "official_brand_domain" in ids_daraz
    assert "lookalike_domain" not in ids_daraz

    # Official Apple
    res_apple = analyze_url_signals("https://www.apple.com/shop/buy-iphone")
    assert res_apple["is_lookalike"] is False
    ids_apple = [s["id"] for s in res_apple["signals"]]
    assert "official_brand_domain" in ids_apple
    assert "lookalike_domain" not in ids_apple


def test_social_media_shop_unverifiable_seller():
    # Instagram shop
    res_ig = analyze_url_signals("https://www.instagram.com/p/C3abcxyz/?utm_source=ig_web_copy_link")
    assert res_ig["is_social_seller"] is True
    assert res_ig["is_lookalike"] is False
    ids_ig = [s["id"] for s in res_ig["signals"]]
    assert "unverifiable_seller" in ids_ig
    # Confirm evidence does NOT call it a scam
    ev = next(s["evidence"] for s in res_ig["signals"] if s["id"] == "unverifiable_seller")
    assert "scam" not in ev.lower() or "not inherently a scam" in ev.lower()

    # WhatsApp link
    res_wa = analyze_url_signals("https://wa.me/923001234567")
    assert res_wa["is_social_seller"] is True
    ids_wa = [s["id"] for s in res_wa["signals"]]
    assert "unverifiable_seller" in ids_wa
