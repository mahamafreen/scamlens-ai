import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

BRANDS_FILE = DATA_DIR / "brands.json"
RETAILERS_FILE = DATA_DIR / "retailers.json"

OLLAMA_BASE_URL = os.getenv("BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("API_KEY", "ollama")
OLLAMA_MODEL = os.getenv("MODEL", "qwen3.5:2b")
VISION_MODEL = os.getenv("VISION_MODEL", "")

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".shop", ".click", ".icu", ".buzz", ".site",
    ".rest", ".vip", ".work", ".cfd", ".monster", ".cam"
}

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "cutt.ly", "rb.gy", "shorturl.at", "bl.ink", "tiny.cc"
}

SOCIAL_PLATFORMS = {
    "instagram.com": "Instagram Shop",
    "facebook.com": "Facebook Marketplace / Shop",
    "fb.me": "Facebook Shortlink",
    "wa.me": "WhatsApp Chat / Shop",
    "whatsapp.com": "WhatsApp Business / Catalog",
    "api.whatsapp.com": "WhatsApp Direct Link",
    "tiktok.com": "TikTok Shop"
}
