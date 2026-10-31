import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx


async def check_domain_age_rdap(domain: str, timeout_seconds: float = 4.0) -> Dict[str, Any]:
    """
    Queries RDAP for domain registration date.
    Returns:
        {
            "status": "known" | "unknown",
            "age_days": Optional[int],
            "registration_date": Optional[str],
            "details": str
        }
    """
    # Clean domain
    clean_domain = domain.lower().strip().rstrip(".")
    if ":" in clean_domain:
        clean_domain = clean_domain.split(":")[0]

    # Don't query RDAP for IP addresses or localhost
    if clean_domain in ("localhost", "127.0.0.1") or re.match(r"^\d+\.\d+\.\d+\.\d+$", clean_domain):
        return {
            "status": "unknown",
            "age_days": None,
            "registration_date": None,
            "details": "RDAP not applicable for IP address or local host"
        }

    url = f"https://rdap.org/domain/{clean_domain}"

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ScamLens-Checker/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                events = data.get("events", [])
                reg_date_str = None
                for ev in events:
                    if ev.get("eventAction") == "registration":
                        reg_date_str = ev.get("eventDate")
                        break

                if reg_date_str:
                    # Parse ISO format: e.g. 2023-01-15T12:00:00Z or 2023-01-15
                    try:
                        clean_dt = reg_date_str.replace("Z", "+00:00")
                        reg_dt = datetime.fromisoformat(clean_dt)
                        now = datetime.now(timezone.utc)
                        age_days = (now - reg_dt).days
                        return {
                            "status": "known",
                            "age_days": max(0, age_days),
                            "registration_date": reg_date_str[:10],
                            "details": f"Registered on {reg_date_str[:10]} ({age_days} days ago)"
                        }
                    except Exception:
                        return {
                            "status": "known",
                            "age_days": None,
                            "registration_date": reg_date_str[:10],
                            "details": f"Registered on {reg_date_str[:10]}"
                        }

                return {
                    "status": "unknown",
                    "age_days": None,
                    "registration_date": None,
                    "details": "RDAP response did not contain a registration date event"
                }

            elif resp.status_code == 404:
                return {
                    "status": "unknown",
                    "age_days": None,
                    "registration_date": None,
                    "details": f"Domain not found in RDAP registry (common for ccTLDs like .pk or unregistered domains)"
                }
            else:
                return {
                    "status": "unknown",
                    "age_days": None,
                    "registration_date": None,
                    "details": f"RDAP lookup returned HTTP {resp.status_code}"
                }
    except httpx.TimeoutException:
        return {
            "status": "unknown",
            "age_days": None,
            "registration_date": None,
            "details": "RDAP lookup timed out (4s limit)"
        }
    except Exception as e:
        return {
            "status": "unknown",
            "age_days": None,
            "registration_date": None,
            "details": f"RDAP check failed: {str(e)}"
        }
