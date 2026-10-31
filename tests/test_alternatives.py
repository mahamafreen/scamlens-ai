import pytest
from app.alternatives import build_comparison_links, clean_query_term


def test_clean_query_term():
    dirty = "Buy iPhone 15 Pro Max 256GB - 70% Off | Best Price in Pakistan!"
    cleaned = clean_query_term(dirty)
    assert "70% Off" not in cleaned
    assert "Best Price in Pakistan" not in cleaned
    assert "iPhone 15 Pro Max 256GB" in cleaned


def test_query_priority():
    # User input wins
    res1 = build_comparison_links(
        user_product_name="Sony WH-1000XM5",
        llm_product_name="Generic Headphones",
        page_title="Headphones page"
    )
    assert res1["search_query"] == "Sony WH-1000XM5"
    assert res1["query_source"] == "user_input"

    # LLM wins when user is empty
    res2 = build_comparison_links(
        user_product_name=None,
        llm_product_name="AirPods Pro 2nd Gen",
        page_title="Clearance Sale"
    )
    assert res2["search_query"] == "AirPods Pro 2nd Gen"
    assert res2["query_source"] == "llm_extraction"

    # Title wins when both user and LLM are empty
    res3 = build_comparison_links(
        user_product_name=None,
        llm_product_name=None,
        page_title="Samsung Galaxy S24 Ultra"
    )
    assert res3["search_query"] == "Samsung Galaxy S24 Ultra"
    assert res3["query_source"] == "page_title"


def test_all_links_from_templates_and_google_site_search():
    res = build_comparison_links(
        user_product_name="Nike Air Jordan 1",
        brand_key="nike"
    )
    links = res["links"]
    assert len(links) >= 4

    # Check each link format
    for link in links:
        url = link["search_url"]
        assert url.startswith("https://www.google.com/search?q=")
        assert "+site:" in url

    # Retailers present
    domains = [l["domain"] for l in links]
    assert "daraz.pk" in domains
    assert "priceoye.pk" in domains
    assert "telemart.pk" in domains
    assert "homeshopping.pk" in domains
    # Official brand domain added
    assert "nike.com" in domains

    # Disclaimer
    assert res["disclaimer"] == "Places to compare - not a guarantee of authenticity or stock"
