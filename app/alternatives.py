import json
import re
from urllib.parse import quote_plus
from typing import Dict, Any, List, Optional
from app.config import RETAILERS_FILE, BRANDS_FILE


def load_retailers() -> List[Dict[str, Any]]:
    if RETAILERS_FILE.exists():
        with open(RETAILERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"name": "Daraz.pk", "domain": "daraz.pk", "url_template": "https://www.google.com/search?q={query}+site:daraz.pk"},
        {"name": "PriceOye.pk", "domain": "priceoye.pk", "url_template": "https://www.google.com/search?q={query}+site:priceoye.pk"},
        {"name": "Telemart.pk", "domain": "telemart.pk", "url_template": "https://www.google.com/search?q={query}+site:telemart.pk"},
        {"name": "HomeShopping.pk", "domain": "homeshopping.pk", "url_template": "https://www.google.com/search?q={query}+site:homeshopping.pk"},
    ]


def load_brands() -> Dict[str, Any]:
    if BRANDS_FILE.exists():
        with open(BRANDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def clean_query_term(text: str) -> str:
    """Cleans excess marketing fluff from product query string."""
    if not text:
        return ""
    # Remove excessive punctuation and brackets
    cleaned = re.sub(r"[\[\](){}|•·!]", " ", text)
    # Remove phrases like "Buy Online in Pakistan", "Best Price", "Sale", "Clearance"
    fluff_patterns = [
        r"\b(?:buy online in pakistan|best price in pakistan|free delivery|cash on delivery|mega sale|discount|clearance)\b",
        r"\b(?:70% off|80% off|50% off|cheap|original 100%|authentic)\b"
    ]
    for pat in fluff_patterns:
        cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # If trimmed too short or empty, revert to original snippet
    return cleaned if len(cleaned) >= 3 else text.strip()


def build_comparison_links(
    user_product_name: Optional[str] = None,
    llm_product_name: Optional[str] = None,
    page_title: Optional[str] = None,
    brand_key: Optional[str] = None,
    brand_claimed: Optional[str] = None
) -> Dict[str, Any]:
    """
    Builds safe Google site-search comparison links from templates in retailers.json.
    NEVER allows the LLM to generate URLs.
    Labels: 'Places to compare - not a guarantee of authenticity or stock'.
    """
    # 1. Determine resolved search query
    query_raw = ""
    source = "none"

    if user_product_name and user_product_name.strip():
        query_raw = user_product_name.strip()
        source = "user_input"
    elif llm_product_name and llm_product_name.strip():
        query_raw = llm_product_name.strip()
        source = "llm_extraction"
    elif page_title and page_title.strip():
        query_raw = page_title.strip()
        source = "page_title"
    else:
        query_raw = (brand_claimed or brand_key or "product").strip()
        source = "brand_fallback"

    query = clean_query_term(query_raw)
    encoded_query = quote_plus(query)

    retailers = load_retailers()
    brands_data = load_brands()

    links: List[Dict[str, str]] = []

    # Add standard trusted retailers from retailers.json
    for ret in retailers:
        name = ret.get("name", ret.get("domain", ""))
        domain = ret.get("domain", "")
        # Template URL
        url = f"https://www.google.com/search?q={encoded_query}+site:{domain}"
        links.append({
            "retailer": name,
            "domain": domain,
            "search_url": url,
            "is_brand_official": False
        })

    # Add official brand domain if recognized in brands.json
    target_brand = brand_key or (brand_claimed.lower() if brand_claimed else None)
    if target_brand and target_brand in brands_data:
        brand_info = brands_data[target_brand]
        official_domains = brand_info.get("official_domains", [])
        if official_domains:
            primary_dom = official_domains[0]
            # Avoid duplicating if already in retailer list
            if not any(l["domain"] == primary_dom for l in links):
                brand_name = brand_info.get("name", target_brand.capitalize())
                links.insert(0, {
                    "retailer": f"{brand_name} Official Domain",
                    "domain": primary_dom,
                    "search_url": f"https://www.google.com/search?q={encoded_query}+site:{primary_dom}",
                    "is_brand_official": True
                })

    return {
        "search_query": query,
        "query_source": source,
        "disclaimer": "Places to compare - not a guarantee of authenticity or stock",
        "links": links
    }
