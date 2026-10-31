import os
import base64
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import (
    BASE_DIR,
    OLLAMA_MODEL,
    VISION_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_API_KEY
)
from app.url_signals import analyze_url_signals, load_brands
from app.rdap_client import check_domain_age_rdap
from app.page_fetcher import fetch_and_parse_page
from app.llm_analyzer import (
    analyze_with_llm,
    check_official_store_claim_mismatch
)
from app.scoring import calculate_risk_score
from app.alternatives import build_comparison_links

app = FastAPI(title="ScamLens: Shop Check", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = BASE_DIR / "static"
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class CheckRequest(BaseModel):
    url: str
    product_name: Optional[str] = None


class AICheckRequest(BaseModel):
    url: str
    hostname: str
    title: str
    visible_text: str
    product_name: Optional[str] = None
    brand_key: Optional[str] = None


@app.get("/", response_class=FileResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>ScamLens Shop Check</h1><p>Frontend static files not loaded yet.</p>")
    return FileResponse(str(index_file))


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": "ScamLens: Shop Check",
        "ollama_model": OLLAMA_MODEL,
        "vision_model_configured": bool(VISION_MODEL)
    }


@app.get("/api/brands")
async def get_brands():
    return load_brands()


async def execute_quick_check(
    url: str,
    product_name: Optional[str] = None,
    image_status: str = "image not used"
) -> Dict[str, Any]:
    # 1. URL Analysis (deterministic)
    url_res = analyze_url_signals(url)
    hostname = url_res["hostname"]
    registered_domain = url_res["domain_info"]["registered_domain"]

    # 2. RDAP Domain Age check
    rdap_res = await check_domain_age_rdap(registered_domain or hostname)

    # 3. Page fetch & parsing (HTML only, no JS)
    page_res = await fetch_and_parse_page(url_res["url"])

    # Initial dummy/fallback LLM state for instant scoring
    initial_llm = {
        "ai_available": False,
        "ai_error": "Pending background analysis",
        "product_name": product_name or page_res.get("title") or "",
        "brand_claimed": "",
        "price_text": "",
        "claims_official_store": False,
        "red_flags": [],
        "missing_trust_info": [],
        "summary": "Analyzing storefront with rules..."
    }

    # 4. Score calculation (fast rules)
    score_res = calculate_risk_score(
        url_analysis=url_res,
        rdap_analysis=rdap_res,
        page_analysis=page_res,
        llm_analysis=initial_llm
    )

    # 5. Alternative comparison links
    alternatives = build_comparison_links(
        user_product_name=product_name,
        llm_product_name=None,
        page_title=page_res.get("title"),
        brand_key=url_res.get("matched_brand"),
        brand_claimed=None
    )

    return {
        "url": url_res["url"],
        "hostname": hostname,
        "product_name": product_name or page_res.get("title") or "",
        "image_status": image_status,
        "score_data": score_res,
        "url_analysis": url_res,
        "rdap_analysis": rdap_res,
        "page_analysis": page_res,
        "alternatives": alternatives,
        "ai_pending": True
    }


@app.post("/api/check-quick")
async def api_check_quick(payload: CheckRequest):
    if not payload.url:
        raise HTTPException(status_code=400, detail="Product link is required")
    return await execute_quick_check(payload.url, payload.product_name)


@app.post("/api/check-ai")
async def api_check_ai(payload: AICheckRequest):
    # Run LLM analysis on extracted page text
    llm_res = await analyze_with_llm(
        url=payload.url,
        hostname=payload.hostname,
        title=payload.title,
        visible_text=payload.visible_text
    )

    # Check official store claim mismatch
    mismatch_signal = check_official_store_claim_mismatch(
        claims_official=llm_res.get("claims_official_store", False),
        brand_claimed=llm_res.get("brand_claimed", ""),
        hostname=payload.hostname
    )

    # Update comparison links if LLM found a clearer product name or brand
    alternatives = build_comparison_links(
        user_product_name=payload.product_name,
        llm_product_name=llm_res.get("product_name"),
        page_title=payload.title,
        brand_key=payload.brand_key,
        brand_claimed=llm_res.get("brand_claimed")
    )

    return {
        "llm_analysis": llm_res,
        "mismatch_signal": mismatch_signal,
        "alternatives": alternatives
    }


@app.post("/check")
async def check_endpoint(
    request: Request,
    url: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """
    Standard full check endpoint.
    Accepts multipart/form-data or application/json.
    Runs complete pipeline: URL signals -> RDAP -> Page Fetch -> LLM extraction -> Scoring -> Alternatives.
    """
    input_url = url
    input_name = product_name
    image_status = "image not used"

    # Handle JSON body if not form data
    if not input_url:
        try:
            body = await request.json()
            input_url = body.get("url")
            input_name = body.get("product_name")
        except Exception:
            pass

    if not input_url:
        raise HTTPException(status_code=400, detail="Product link is required")

    # Optional stretch: vision model
    if image is not None and VISION_MODEL:
        image_status = f"vision model configured ({VISION_MODEL})"
    elif image is not None:
        image_status = "image not used (VISION_MODEL not set)"

    # 1. URL Analysis
    url_res = analyze_url_signals(input_url)
    hostname = url_res["hostname"]
    registered_domain = url_res["domain_info"]["registered_domain"]

    # 2. RDAP Domain Age
    rdap_res = await check_domain_age_rdap(registered_domain or hostname)

    # 3. Page fetch & parsing
    page_res = await fetch_and_parse_page(url_res["url"])

    # 4. LLM Analysis
    llm_res = await analyze_with_llm(
        url=url_res["url"],
        hostname=hostname,
        title=page_res.get("title", ""),
        visible_text=page_res.get("visible_text", "")
    )

    # Check official store claim mismatch
    mismatch_signal = check_official_store_claim_mismatch(
        claims_official=llm_res.get("claims_official_store", False),
        brand_claimed=llm_res.get("brand_claimed", ""),
        hostname=hostname
    )

    # 5. Score calculation
    score_res = calculate_risk_score(
        url_analysis=url_res,
        rdap_analysis=rdap_res,
        page_analysis=page_res,
        llm_analysis=llm_res,
        claim_mismatch_signal=mismatch_signal
    )

    # 6. Alternatives
    alternatives = build_comparison_links(
        user_product_name=input_name,
        llm_product_name=llm_res.get("product_name"),
        page_title=page_res.get("title"),
        brand_key=url_res.get("matched_brand"),
        brand_claimed=llm_res.get("brand_claimed")
    )

    return {
        "url": url_res["url"],
        "hostname": hostname,
        "product_name": input_name or llm_res.get("product_name") or page_res.get("title") or "",
        "image_status": image_status,
        "score_data": score_res,
        "url_analysis": url_res,
        "rdap_analysis": rdap_res,
        "page_analysis": page_res,
        "llm_analysis": llm_res,
        "alternatives": alternatives,
        "ai_pending": False
    }
