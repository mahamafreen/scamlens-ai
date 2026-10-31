import json
import re
import ipaddress
from urllib.parse import urlparse
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

from app.config import (
    BRANDS_FILE,
    SUSPICIOUS_TLDS,
    URL_SHORTENERS,
    SOCIAL_PLATFORMS,
)


@dataclass
class Signal:
    id: str
    title: str
    severity: str  # "high", "medium", "low", "info", "positive"
    score_weight: int
    evidence: str
    is_risk: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_brands() -> Dict[str, Any]:
    if BRANDS_FILE.exists():
        with open(BRANDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def normalize_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def extract_domain_parts(hostname: str) -> Dict[str, Any]:
    hostname = hostname.lower().strip().rstrip(".")
    # Remove port if present
    if ":" in hostname:
        hostname = hostname.split(":")[0]

    # Split labels
    labels = hostname.split(".")
    # Basic second-level domain support (e.g. .com.pk, .org.pk, .co.uk)
    two_part_tlds = {"com.pk", "org.pk", "net.pk", "gov.pk", "edu.pk", "co.uk", "com.bd", "com.np"}
    
    tld = ""
    domain_stem = hostname
    registered_domain = hostname

    if len(labels) >= 3 and f"{labels[-2]}.{labels[-1]}" in two_part_tlds:
        tld = f".{labels[-2]}.{labels[-1]}"
        domain_stem = labels[-3]
        registered_domain = f"{labels[-3]}.{labels[-2]}.{labels[-1]}"
    elif len(labels) >= 2:
        tld = f".{labels[-1]}"
        domain_stem = labels[-2]
        registered_domain = f"{labels[-2]}.{labels[-1]}"
    elif len(labels) == 1:
        domain_stem = labels[0]

    return {
        "hostname": hostname,
        "labels": labels,
        "tld": tld,
        "domain_stem": domain_stem,
        "registered_domain": registered_domain,
    }


def analyze_url_signals(raw_url: str, brands_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if brands_data is None:
        brands_data = load_brands()

    clean_url = normalize_url(raw_url)
    parsed = urlparse(clean_url)
    hostname = (parsed.hostname or "").lower()

    signals: List[Signal] = []
    is_social_seller = False
    is_lookalike = False
    matched_brand: Optional[str] = None

    domain_info = extract_domain_parts(hostname)
    labels = domain_info["labels"]
    tld = domain_info["tld"]
    domain_stem = domain_info["domain_stem"]
    registered_domain = domain_info["registered_domain"]

    # 1. HTTPS or not
    if parsed.scheme != "https":
        signals.append(
            Signal(
                id="insecure_http",
                title="Unencrypted HTTP Connection",
                severity="medium",
                score_weight=15,
                evidence=f"The URL uses unencrypted '{parsed.scheme}://'. Legitimate online stores require HTTPS to safeguard credentials and payment details."
            )
        )

    # 2. IP address host
    is_ip = False
    try:
        ipaddress.ip_address(hostname)
        is_ip = True
    except ValueError:
        is_ip = False

    if is_ip:
        signals.append(
            Signal(
                id="ip_address_host",
                title="Direct IP Address Host",
                severity="high",
                score_weight=40,
                evidence=f"Host is a raw IP address ({hostname}) rather than a registered domain name. Legitimate e-commerce retailers never host shops on raw IP addresses."
            )
        )

    # 3. Punycode / IDN
    is_punycode = "xn--" in hostname or any(ord(char) > 127 for char in hostname)
    if is_punycode:
        signals.append(
            Signal(
                id="punycode_host",
                title="Punycode / Internationalized Domain Name",
                severity="high",
                score_weight=30,
                evidence=f"Domain '{hostname}' contains internationalized/punycode characters, commonly used in homograph attacks to impersonate well-known websites."
            )
        )

    # 4. Shortened URL check
    is_shortener = False
    for shortener in URL_SHORTENERS:
        if hostname == shortener or hostname.endswith("." + shortener):
            is_shortener = True
            signals.append(
                Signal(
                    id="shortened_url",
                    title="Shortened URL Service",
                    severity="low",
                    score_weight=10,
                    evidence=f"Host '{hostname}' is a URL shortener, masking the real product destination domain."
                )
            )
            break

    # 5. Suspicious TLD check
    if any(hostname.endswith(stld) for stld in SUSPICIOUS_TLDS):
        signals.append(
            Signal(
                id="suspicious_tld",
                title="Suspicious or Cheap TLD",
                severity="low",
                score_weight=15,
                evidence=f"Domain uses TLD '{tld}', which has high abuse rates among ephemeral scam stores (weak signal on its own)."
            )
        )

    # 6. Excessive hyphens or digits
    hyphen_count = hostname.count("-")
    if hyphen_count >= 2:
        signals.append(
            Signal(
                id="excessive_hyphens",
                title="Multiple Hyphens in Domain",
                severity="medium",
                score_weight=15,
                evidence=f"Domain contains {hyphen_count} hyphens ('{hostname}'). Fraudulent stores frequently string together brand and shopping keywords with hyphens."
            )
        )

    # Count digits in domain stem
    digit_count = sum(c.isdigit() for c in domain_stem)
    if digit_count >= 3:
        signals.append(
            Signal(
                id="excessive_digits",
                title="High Digit Count in Domain Name",
                severity="low",
                score_weight=10,
                evidence=f"Domain label '{domain_stem}' contains {digit_count} digits, which is characteristic of automated or disposable domain registrations."
            )
        )

    # 7. Instagram/Facebook/WhatsApp shop pages (Flag as "unverifiable seller", not "scam")
    for platform_domain, platform_desc in SOCIAL_PLATFORMS.items():
        if hostname == platform_domain or hostname.endswith("." + platform_domain):
            is_social_seller = True
            signals.append(
                Signal(
                    id="unverifiable_seller",
                    title="Unverifiable Seller (Social Media / Messaging)",
                    severity="medium",
                    score_weight=25,
                    evidence=f"URL directs to {platform_desc}. Social media and chat platforms lack merchant verification, formal return dispute systems, and payment escrow. While not inherently a scam, sellers cannot be verified independently."
                )
            )
            break

    # 8. LOOKALIKE detection against brands.json
    # Only run lookalike detection if not already identified as a generic social platform
    if not is_social_seller and not is_ip:
        for brand_key, brand_info in brands_data.items():
            b_name = brand_info.get("name", brand_key.capitalize())
            official_domains = [d.lower() for d in brand_info.get("official_domains", [])]

            # Check if this hostname is actually an authorized official domain of the brand
            is_official = False
            for off_dom in official_domains:
                if hostname == off_dom or hostname.endswith("." + off_dom):
                    is_official = True
                    matched_brand = brand_key
                    break

            if is_official:
                # This domain is officially recognized for this brand!
                signals.append(
                    Signal(
                        id="official_brand_domain",
                        title=f"Recognized Official Domain for {b_name}",
                        severity="positive",
                        score_weight=0,
                        evidence=f"Domain '{hostname}' matches the officially verified domain for {b_name} ({', '.join(official_domains)}).",
                        is_risk=False
                    )
                )
                break

            # If not official: does the brand name appear inside the domain or domain stem?
            # E.g. "daraz" in "daraz-deals.com", "nike" in "nike-shoes-pk.shop", "apple" in "apple-support.xyz"
            # We want to match exact word tokens or substrings (avoid false matching "apple" in "snapple.com")
            brand_token_pattern = rf"(^|[-_.0-9]){re.escape(brand_key)}([-_.0-9]|$)"
            contains_brand = bool(re.search(brand_token_pattern, hostname)) or (brand_key in domain_stem and len(brand_key) >= 5)

            if contains_brand:
                is_lookalike = True
                matched_brand = brand_key
                signals.append(
                    Signal(
                        id="lookalike_domain",
                        title=f"Lookalike Domain Detected ({b_name})",
                        severity="high",
                        score_weight=50,
                        evidence=f"The domain '{hostname}' contains the well-known brand '{b_name}', but is NOT an authorized domain for that brand. Official domains: {', '.join(official_domains)}."
                    )
                )
                break

            # Typo-squatting detection on domain stem (e.g., 'daeraz' for 'daraz', 'aple' for 'apple')
            # Only test if domain stem is of comparable length
            if abs(len(domain_stem) - len(brand_key)) <= 1 and len(brand_key) >= 4:
                dist = levenshtein_distance(domain_stem, brand_key)
                if dist == 1:
                    is_lookalike = True
                    matched_brand = brand_key
                    signals.append(
                        Signal(
                            id="typosquat_lookalike",
                            title=f"Potential Typosquatting of {b_name}",
                            severity="high",
                            score_weight=45,
                            evidence=f"The domain name '{domain_stem}' is an apparent misspelling of '{b_name}' (distance 1 edit). Scammers use typosquatting to mimic legitimate storefronts."
                        )
                    )
                    break

    return {
        "url": clean_url,
        "hostname": hostname,
        "domain_info": domain_info,
        "is_social_seller": is_social_seller,
        "is_lookalike": is_lookalike,
        "is_shortener": is_shortener,
        "matched_brand": matched_brand,
        "signals": [s.to_dict() for s in signals],
    }

