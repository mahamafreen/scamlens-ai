import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup


BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

PRICE_REGEX = re.compile(
    r"(?:(?:Rs\.?|PKR|USD|\$|EUR|£)\s*[\d,]+(?:\.\d{2})?|[\d,]+\s*(?:PKR|Rs\.?))",
    re.IGNORECASE
)

PHONE_REGEX = re.compile(
    r"(?:(?:\+?92|0)[3-9]\d{2}[\s-]?\d{7}|\b\d{3,4}[-.\s]\d{3,4}[-.\s]\d{3,4}\b)"
)

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

ADDRESS_KEYWORDS = [
    "address", "head office", "branch", "located at", "floor", "plaza", "building",
    "street", "road", "karachi", "lahore", "islamabad", "rawalpindi", "peshawar",
    "faisalabad", "multan", "postal code", "p.o. box"
]

POLICY_KEYWORDS = [
    "return policy", "refund policy", "returns & refunds", "exchange policy",
    "warranty policy", "money back guarantee", "return & exchange", "cancellation policy"
]

ABOUT_KEYWORDS = [
    "about us", "who we are", "our story", "company profile", "about the company",
    "contact us", "reach us"
]


async def fetch_and_parse_page(url: str, timeout_seconds: float = 8.0) -> Dict[str, Any]:
    """
    Fetches HTML page and extracts metadata, visible text, prices, and trust indicators.
    Enforces 8s timeout, max 5 redirects, max 1MB size, HTML only.
    """
    result: Dict[str, Any] = {
        "page_readable": False,
        "final_url": url,
        "final_domain": "",
        "status_code": None,
        "error_reason": None,
        "title": "",
        "og_title": "",
        "meta_description": "",
        "visible_text": "",
        "price_strings": [],
        "contact_info": {
            "phones": [],
            "emails": [],
            "address_found": False,
            "address_snippet": ""
        },
        "has_refund_policy": False,
        "has_about_page": False,
        "payment_signals": {
            "cod_detected": False,
            "bank_transfer_only": False,
            "crypto_detected": False,
            "gift_cards_detected": False,
            "details": []
        }
    }

    try:
        parsed_init = urlparse(url)
        result["final_domain"] = parsed_init.hostname or ""

        headers = {
            "User-Agent": BROWSER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ur;q=0.8",
        }

        # Follow up to 5 redirects
        transport = httpx.AsyncHTTPTransport(retries=1)
        async with httpx.AsyncClient(transport=transport, timeout=timeout_seconds, follow_redirects=True, max_redirects=5) as client:
            resp = await client.get(url, headers=headers)
            result["status_code"] = resp.status_code
            result["final_url"] = str(resp.url)
            result["final_domain"] = urlparse(result["final_url"]).hostname or ""

            # Check content length (max 1MB = 1,048,576 bytes)
            content_length = resp.headers.get("content-length")
            if content_length and int(content_length) > 1048576:
                result["error_reason"] = "Page exceeds 1MB limit"
                return result

            # Content type check: must be HTML
            content_type = resp.headers.get("content-type", "").lower()
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                result["error_reason"] = f"Non-HTML content type ({content_type or 'unknown'})"
                return result

            if resp.status_code >= 400:
                result["error_reason"] = f"Server returned HTTP {resp.status_code}"
                return result

            body_bytes = resp.content
            if len(body_bytes) > 1048576:
                body_bytes = body_bytes[:1048576]

            html_text = resp.text

    except httpx.TooManyRedirects:
        result["error_reason"] = "Exceeded maximum of 5 redirects"
        return result
    except httpx.TimeoutException:
        result["error_reason"] = f"Connection timed out after {timeout_seconds}s"
        return result
    except httpx.RequestError as e:
        result["error_reason"] = f"Connection error: {str(e)}"
        return result
    except Exception as e:
        result["error_reason"] = f"Fetch failed: {str(e)}"
        return result

    # Parsing with BeautifulSoup
    try:
        soup = BeautifulSoup(html_text, "html.parser")

        # Title
        title_el = soup.find("title")
        result["title"] = title_el.get_text().strip() if title_el else ""

        # og:title
        og_el = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
        result["og_title"] = og_el.get("content", "").strip() if og_el else ""

        # meta description
        desc_el = (
            soup.find("meta", attrs={"name": "description"}) or
            soup.find("meta", attrs={"property": "og:description"}) or
            soup.find("meta", attrs={"name": "twitter:description"})
        )
        result["meta_description"] = desc_el.get("content", "").strip() if desc_el else ""

        # Strip non-text elements
        for element in soup(["script", "style", "noscript", "svg", "symbol"]):
            element.decompose()

        full_text = soup.get_text(separator=" ", strip=True)
        # Normalize whitespace
        full_text = re.sub(r"\s+", " ", full_text).strip()

        # Check for JS-only / empty page
        if len(full_text) < 70 or "javascript is disabled" in full_text.lower() or "enable javascript" in full_text.lower():
            result["error_reason"] = "Page is JavaScript-rendered (no readable server HTML)"
            result["visible_text"] = full_text[:1000]
            return result

        result["visible_text"] = full_text[:3000]
        result["page_readable"] = True

        # Extract prices
        found_prices = PRICE_REGEX.findall(full_text)
        # Deduplicate while preserving order
        unique_prices = []
        for p in found_prices:
            p_clean = p.strip()
            if p_clean not in unique_prices:
                unique_prices.append(p_clean)
        result["price_strings"] = unique_prices[:6]

        # Extract contact info
        text_lower = full_text.lower()
        phones = PHONE_REGEX.findall(full_text)
        result["contact_info"]["phones"] = list(dict.fromkeys(phones))[:4]

        emails = EMAIL_REGEX.findall(full_text)
        # Filter out common assets or fake image extensions in email regex
        clean_emails = [e for e in emails if not e.endswith((".png", ".jpg", ".webp", ".svg", ".js"))]
        result["contact_info"]["emails"] = list(dict.fromkeys(clean_emails))[:3]

        # Physical address keywords
        for kw in ADDRESS_KEYWORDS:
            if kw in text_lower:
                result["contact_info"]["address_found"] = True
                idx = text_lower.find(kw)
                start = max(0, idx - 20)
                end = min(len(full_text), idx + 100)
                result["contact_info"]["address_snippet"] = full_text[start:end].strip()
                break

        # Returns/refund policy
        # Also check <a> link texts and hrefs
        links = soup.find_all("a", href=True)
        link_texts = " ".join([a.get_text() + " " + a["href"] for a in links]).lower()

        for p_kw in POLICY_KEYWORDS:
            if p_kw in text_lower or p_kw in link_texts:
                result["has_refund_policy"] = True
                break

        # About page / contact page
        for a_kw in ABOUT_KEYWORDS:
            if a_kw in text_lower or a_kw in link_texts:
                result["has_about_page"] = True
                break

        # Payment checks
        pay_details = []
        if any(w in text_lower for w in ["cash on delivery", "cod available", "pay upon delivery", "payment on delivery"]):
            result["payment_signals"]["cod_detected"] = True
            pay_details.append("Cash on Delivery (COD) supported")

        if any(w in text_lower for w in ["bank transfer only", "advance payment only", "direct bank transfer required", "advance full payment"]):
            result["payment_signals"]["bank_transfer_only"] = True
            pay_details.append("Warning: Demands Advance Bank Transfer Only")

        if any(w in text_lower for w in ["bitcoin", "crypto payment", "usdt", "binance pay", "pay via btc"]):
            result["payment_signals"]["crypto_detected"] = True
            pay_details.append("Suspicious: Cryptocurrency payment requested")

        if any(w in text_lower for w in ["gift card only", "pay with apple gift card", "steam card payment", "amazon gift card code"]):
            result["payment_signals"]["gift_cards_detected"] = True
            pay_details.append("Severe Risk: Demands Gift Cards as payment")

        result["payment_signals"]["details"] = pay_details

    except Exception as e:
        result["error_reason"] = f"HTML parsing error: {str(e)}"

    return result
