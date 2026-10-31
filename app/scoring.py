from typing import Dict, Any, List


def calculate_risk_score(
    url_analysis: Dict[str, Any],
    rdap_analysis: Dict[str, Any],
    page_analysis: Dict[str, Any],
    llm_analysis: Dict[str, Any],
    claim_mismatch_signal: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Computes a risk score from 0 to 100 based on weighted signals.
    Never refers to the score as a 'probability' or 'guarantee'.
    Enforces rule: Missing information must never lower the score below Medium
    (minimum 45) when a lookalike or very new domain is detected.
    """
    signals: List[Dict[str, Any]] = []
    
    # 1. URL Signals
    url_signals = url_analysis.get("signals", [])
    signals.extend(url_signals)

    is_lookalike = url_analysis.get("is_lookalike", False)
    is_official_brand = any(s.get("id") == "official_brand_domain" for s in url_signals)

    # 2. RDAP Domain Age Signals
    rdap_status = rdap_analysis.get("status", "unknown")
    age_days = rdap_analysis.get("age_days")
    is_very_new_domain = False

    if rdap_status == "known" and age_days is not None:
        if age_days < 90:
            is_very_new_domain = True
            signals.append({
                "id": "domain_age_under_90_days",
                "title": "Extremely New Domain (< 90 Days)",
                "severity": "high",
                "score_weight": 35,
                "evidence": f"Domain was registered only {age_days} days ago ({rdap_analysis.get('registration_date')}). Fraudulent storefronts are overwhelmingly hosted on newly registered domains.",
                "is_risk": True
            })
        elif age_days < 365:
            signals.append({
                "id": "domain_age_under_365_days",
                "title": "Recently Registered Domain (< 1 Year)",
                "severity": "medium",
                "score_weight": 15,
                "evidence": f"Domain was registered {age_days} days ago ({rdap_analysis.get('registration_date')}). Relatively recent domain registration.",
                "is_risk": True
            })
        else:
            # Established domain
            signals.append({
                "id": "domain_age_established",
                "title": "Established Domain History",
                "severity": "positive",
                "score_weight": -10,
                "evidence": f"Domain has an established registration history of {age_days} days ({rdap_analysis.get('registration_date')}). Established domains carry lower scam risk.",
                "is_risk": False
            })
    else:
        # Unknown domain age: only a tiny weight (e.g. 3)
        signals.append({
            "id": "domain_age_unknown",
            "title": "Domain Age Unknown via RDAP",
            "severity": "info",
            "score_weight": 3,
            "evidence": f"Domain age could not be resolved from public RDAP registries ({rdap_analysis.get('details', 'no record')}). Many national domains (such as .pk) omit public RDAP data.",
            "is_risk": True
        })

    # 3. Page Content Signals (only apply penalties if page was readable)
    page_readable = page_analysis.get("page_readable", False)
    if page_readable:
        payment = page_analysis.get("payment_signals", {})
        contact = page_analysis.get("contact_info", {})
        has_refund = page_analysis.get("has_refund_policy", False)
        has_about = page_analysis.get("has_about_page", False)

        # Payment red flags
        if payment.get("gift_cards_detected"):
            signals.append({
                "id": "payment_gift_cards",
                "title": "High Risk Payment: Gift Cards Requested",
                "severity": "high",
                "score_weight": 40,
                "evidence": "Storefront solicits payment via gift cards. Legitimate retailers never mandate gift card codes for product purchases.",
                "is_risk": True
            })

        if payment.get("crypto_detected"):
            signals.append({
                "id": "payment_crypto_demanded",
                "title": "Cryptocurrency Payment Requested",
                "severity": "high",
                "score_weight": 25,
                "evidence": "Storefront solicits payment via cryptocurrency (Bitcoin/USDT). Irreversible crypto transfers remove all chargeback protection.",
                "is_risk": True
            })

        if payment.get("bank_transfer_only"):
            signals.append({
                "id": "payment_advance_bank_transfer_only",
                "title": "Advance Bank Transfer Only Required",
                "severity": "medium",
                "score_weight": 20,
                "evidence": "Storefront mandates advance bank transfer or WhatsApp slips with no escrow or Cash on Delivery protection.",
                "is_risk": True
            })

        # COD positive signal
        if payment.get("cod_detected") and not is_lookalike:
            signals.append({
                "id": "payment_cod_available",
                "title": "Cash on Delivery (COD) Supported",
                "severity": "positive",
                "score_weight": -10,
                "evidence": "Storefront explicitly supports Cash on Delivery, allowing buyers to inspect packaging before paying.",
                "is_risk": False
            })

        # Missing contact information
        has_any_contact = bool(contact.get("phones") or contact.get("emails") or contact.get("address_found"))
        if not has_any_contact and not is_official_brand:
            signals.append({
                "id": "missing_contact_info",
                "title": "No Direct Contact Info or Physical Address",
                "severity": "medium",
                "score_weight": 15,
                "evidence": "No valid phone numbers, customer support email addresses, or physical office address were located on the page text.",
                "is_risk": True
            })

        # Missing refund policy
        if not has_refund and not is_official_brand:
            signals.append({
                "id": "missing_refund_policy",
                "title": "Missing Return / Refund Policy",
                "severity": "low",
                "score_weight": 10,
                "evidence": "No formal return, refund, or exchange policy links or text could be detected on the page.",
                "is_risk": True
            })

    # 4. LLM Signals & Official Store Mismatch
    if claim_mismatch_signal:
        signals.append(claim_mismatch_signal)

    if llm_analysis.get("ai_available"):
        red_flags = llm_analysis.get("red_flags", [])
        for idx, rf in enumerate(red_flags[:3]):
            signals.append({
                "id": f"llm_flag_{idx+1}",
                "title": "AI Flag: Suspicious Storefront Feature",
                "severity": "medium",
                "score_weight": 10,
                "evidence": f"AI extraction noted: {rf}",
                "is_risk": True
            })

        missing_info = llm_analysis.get("missing_trust_info", [])
        for idx, mi in enumerate(missing_info[:2]):
            signals.append({
                "id": f"llm_missing_{idx+1}",
                "title": "AI Flag: Trust Deficit",
                "severity": "low",
                "score_weight": 5,
                "evidence": f"AI noted missing trust signal: {mi}",
                "is_risk": True
            })

    # Official domain discount: If domain is a verified official brand domain (e.g. apple.com, daraz.pk),
    # mitigate minor missing text warnings (e.g. short product page that doesn't embed policy in body).
    if is_official_brand:
        # Keep score near low
        raw_score = 5
    else:
        # Sum all score weights
        raw_score = sum(s.get("score_weight", 0) for s in signals)

    # Enforce minimum threshold if lookalike or very new domain
    # "Missing information must never lower the score below Medium when a lookalike or very new domain is detected."
    if is_lookalike or is_very_new_domain:
        raw_score = max(raw_score, 45)

    # Clamp 0 - 100
    final_score = max(0, min(100, raw_score))

    # Label calculation:
    # 0-33 Low, 34-66 Medium, 67-100 High
    if final_score <= 33:
        label = "Low"
        label_text = "Low Risk"
        color = "#10b981"  # green
    elif final_score <= 66:
        label = "Medium"
        label_text = "Medium Risk"
        color = "#f59e0b"  # amber
    else:
        label = "High"
        label_text = "High Risk"
        color = "#ef4444"  # red

    # Summary explanation
    risk_signals = [s for s in signals if s.get("is_risk", True) and s.get("score_weight", 0) > 0]
    positive_signals = [s for s in signals if not s.get("is_risk", True) or s.get("score_weight", 0) <= 0]

    # Audit checklist: "What we could and could not check"
    audit_checks = [
        {
            "name": "URL Structure & Brand Directory",
            "checked": True,
            "status": "Lookalike impersonation detected!" if is_lookalike else ("Verified official domain" if is_official_brand else "Checked (no brand conflict)"),
            "success": not is_lookalike
        },
        {
            "name": "Domain Age (RDAP Registry)",
            "checked": rdap_status == "known",
            "status": rdap_analysis.get("details", "Checked"),
            "success": rdap_status == "known" and (age_days is None or age_days >= 90)
        },
        {
            "name": "Live Page Content & Policies",
            "checked": page_readable,
            "status": "HTML parsed successfully (policies & contact details inspected)" if page_readable else f"Page unreadable: {page_analysis.get('error_reason', 'network/format issue')}",
            "success": page_readable
        },
        {
            "name": "AI Text Extraction (Ollama)",
            "checked": llm_analysis.get("ai_available", False),
            "status": "Ollama LLM analyzed claims & trust indicators" if llm_analysis.get("ai_available") else f"AI unavailable ({llm_analysis.get('ai_error', 'offline')})",
            "success": llm_analysis.get("ai_available", False)
        }
    ]

    return {
        "score": final_score,
        "label": label,
        "label_text": label_text,
        "color": color,
        "disclaimer": "Warning signs, not proof. Never share OTPs or card details.",
        "signals": signals,
        "risk_signals": risk_signals,
        "positive_signals": positive_signals,
        "audit_checks": audit_checks
    }
