import json
import re
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI

from app.config import (
    OLLAMA_BASE_URL,
    OLLAMA_API_KEY,
    OLLAMA_MODEL,
    VISION_MODEL
)
from app.url_signals import load_brands


def clean_think_blocks(text: str) -> str:
    """Removes <think>...</think> blocks from LLM responses."""
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.DOTALL)
    # Also handle unclosed <think> tag if output was cut off
    cleaned = re.sub(r"<think>[\s\S]*$", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()


def extract_json_from_llm(raw_text: str) -> Optional[Dict[str, Any]]:
    """Attempts to parse JSON object from LLM output, handling markdown code fences."""
    text = clean_think_blocks(raw_text).strip()
    
    # Strip markdown code blocks if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # Try direct parse
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Try finding the first '{' and last '}'
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return None


async def analyze_with_llm(
    url: str,
    hostname: str,
    title: str,
    visible_text: str,
    timeout_seconds: float = 12.0
) -> Dict[str, Any]:
    """
    Calls Ollama LLM to extract product info, claims, and scam indicators.
    Returns:
        {
            "ai_available": bool,
            "ai_error": Optional[str],
            "product_name": str,
            "brand_claimed": str,
            "price_text": str,
            "claims_official_store": bool,
            "red_flags": List[str],
            "missing_trust_info": List[str],
            "summary": str
        }
    """
    fallback_result: Dict[str, Any] = {
        "ai_available": False,
        "ai_error": None,
        "product_name": title or "",
        "brand_claimed": "",
        "price_text": "",
        "claims_official_store": False,
        "red_flags": [],
        "missing_trust_info": [],
        "summary": "AI analysis unavailable (using rule-based evaluation)."
    }

    if not visible_text and not title:
        fallback_result["ai_error"] = "No readable page text available for AI analysis"
        return fallback_result

    prompt = f"""You are ScamLens Shop Check assistant. Analyze this product page snippet from domain '{hostname}'.
Page Title: {title}
Page Text:
{visible_text[:2000]}

Extract scam indicators and return ONLY valid JSON with these exact keys:
{{
  "product_name": "identified product name or empty string",
  "brand_claimed": "brand name mentioned (e.g. Apple, Nike, Daraz, Samsung) or empty string",
  "price_text": "price if visible or empty string",
  "claims_official_store": true/false (true ONLY if text explicitly claims to be the official brand store or authorized distributor),
  "red_flags": ["short bullet strings for unusual claims, fake discounts, urgent timers, suspicious payment, etc"],
  "missing_trust_info": ["short bullet strings for missing refund, contact, or company info"],
  "summary": "1-2 sentence assessment in simple English (add Roman Urdu if text is in Urdu)"
}}"""

    system_instruction = (
        "You are an e-commerce safety analyst. Output strictly valid JSON without explanation. "
        "Explain in simple English (add Roman Urdu if page text is in Urdu). Strip hype."
    )

    try:
        client = AsyncOpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key=OLLAMA_API_KEY,
            timeout=timeout_seconds
        )

        response = await client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=250
        )

        raw_content = response.choices[0].message.content or ""
        parsed_json = extract_json_from_llm(raw_content)

        if not parsed_json:
            fallback_result["ai_error"] = "Model returned non-JSON response"
            return fallback_result

        return {
            "ai_available": True,
            "ai_error": None,
            "product_name": str(parsed_json.get("product_name") or title or "").strip(),
            "brand_claimed": str(parsed_json.get("brand_claimed") or "").strip(),
            "price_text": str(parsed_json.get("price_text") or "").strip(),
            "claims_official_store": bool(parsed_json.get("claims_official_store", False)),
            "red_flags": [str(x) for x in parsed_json.get("red_flags", []) if x][:5],
            "missing_trust_info": [str(x) for x in parsed_json.get("missing_trust_info", []) if x][:5],
            "summary": str(parsed_json.get("summary") or "").strip()
        }

    except Exception as e:
        fallback_result["ai_error"] = f"LLM unavailable: {str(e)}"
        return fallback_result


def check_official_store_claim_mismatch(
    claims_official: bool,
    brand_claimed: str,
    hostname: str,
    brands_data: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Checks if page claims to be the official store of a brand,
    but the domain does not match that brand's official domain.
    """
    if not claims_official or not brand_claimed:
        return None

    if brands_data is None:
        brands_data = load_brands()

    hostname_clean = hostname.lower()
    b_claimed_clean = brand_claimed.lower().strip()

    # Find brand in brands.json
    matched_brand_info = None
    for k, info in brands_data.items():
        if k == b_claimed_clean or info.get("name", "").lower() == b_claimed_clean:
            matched_brand_info = info
            break

    if matched_brand_info:
        official_domains = [d.lower() for d in matched_brand_info.get("official_domains", [])]
        is_official = any(hostname_clean == d or hostname_clean.endswith("." + d) for d in official_domains)
        if not is_official:
            return {
                "id": "official_store_claim_mismatch",
                "title": f"Unauthorized Official Store Claim for {matched_brand_info.get('name')}",
                "severity": "high",
                "score_weight": 35,
                "evidence": (
                    f"Page claims to be the official store / authorized seller of '{matched_brand_info.get('name')}', "
                    f"but domain '{hostname}' does not match official domain(s): {', '.join(official_domains)}."
                ),
                "is_risk": True
            }
    else:
        # Brand not in brands.json, but claims official store on a third-party domain
        # If brand name is not in domain at all
        if b_claimed_clean not in hostname_clean:
            return {
                "id": "official_store_claim_unverified",
                "title": f"Unverified Official Store Claim ({brand_claimed})",
                "severity": "medium",
                "score_weight": 25,
                "evidence": (
                    f"Page claims to be the official store for '{brand_claimed}', "
                    f"but domain '{hostname}' does not appear to belong to this brand."
                ),
                "is_risk": True
            }

    return None
