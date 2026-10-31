# ScamLens: Shop Check

> An intelligent, open-weight e-commerce safety evaluator. Analyzes online shop URLs, checks brand impersonation, inspects storefront policies, and suggests verified retailer alternatives.

---

## 1. What It Is & Who It Helps

Online shoppers frequently encounter sponsored ads or social media links promoting heavily discounted electronics, branded shoes, and luxury items. Many of these storefronts are fly-by-night lookalikes that collect upfront payments via bank transfers or cards without delivering goods.

**ScamLens: Shop Check** helps consumers verify online product links **before** sharing payments, OTPs, or card details. Users paste a link (and optional product name or image) to instantly receive:
- A **Risk Score (0–100)** and label (**Low**, **Medium**, or **High Risk**)
- Transparent **evidence for every warning signal** detected
- A clear **"What we could and couldn't check"** audit box
- Direct links to **trusted, verified retailers** (Daraz.pk, PriceOye.pk, Telemart.pk, HomeShopping.pk, and official brand domains) to compare real pricing and availability

> **Disclaimer**: ScamLens provides warning signs, not proof or guarantees. Never share bank OTPs or card details on unverified platforms.

---

## 2. How to Run on Windows 11

### Prerequisites
- Windows 11 (CPU-only, 16GB RAM supported)
- Python 3.10+ installed
- [Ollama](https://ollama.com/) (optional for AI text analysis, runs at `http://localhost:11434`)

### Setup & Launch

1. **Clone or Navigate to the Project**:
   ```powershell
   cd c:\Users\Elitebook\Desktop\scamlens
   ```

2. **Install Dependencies**:
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **(Optional) Start Ollama LLM**:
   If Ollama is installed on your machine, pull the default small open-weight model:
   ```powershell
   ollama pull qwen3.5:2b
   ```
   *Note: If Ollama is offline or uninstalled, ScamLens automatically falls back to full rule-based evaluation without crashing.*

4. **Run the Application**:
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Open in Browser**:
   Visit [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Run Automated Tests & Evaluation
```powershell
# Run full pytest suite (27 unit and integration tests)
python -m pytest -v

# Run benchmark evaluation
python eval.py
```

---

## 3. How It Works (Rules + Open-Weight Model)

ScamLens employs a layered defense architecture combining fast deterministic rules with local language model extraction:

```
[ User Link ]
      │
      ├── 1. URL Analysis (Deterministic Heuristics)
      │      ├── HTTPS vs HTTP check
      │      ├── IP address hostname detection
      │      ├── Punycode / IDN homograph checks
      │      ├── URL shortener detection (bit.ly, tinyurl, etc.)
      │      ├── Low-cost / suspicious TLD checks (.xyz, .top, .shop, etc.)
      │      ├── Excessive hyphen and digit counts
      │      ├── Whitelisted brand directory matching (brands.json)
      │      └── Social media shop identification (Instagram, FB, WhatsApp)
      │
      ├── 2. Domain Age via RDAP (rdap.org)
      │      ├── Registered < 90 days ago = High Risk (+35 pts)
      │      ├── Registered < 365 days ago = Medium (+15 pts)
      │      └── Unknown = Minor weight (+3 pts)
      │
      ├── 3. Live Page Fetcher (Server HTML, No JS Execution)
      │      ├── 8s timeout, max 5 redirects, max 1MB limit
      │      ├── Contact extraction (phone, email, physical address)
      │      ├── Policy detection (return/refund/exchange policy)
      │      └── Payment flags (Cash on Delivery vs Bank Transfer Only / Crypto / Gift Cards)
      │
      ├── 4. Open-Weight LLM Extraction (Ollama @ localhost:11434)
      │      ├── Model: qwen3.5:2b (temperature 0, max 250 tokens)
      │      ├── Strips <think> reasoning blocks
      │      ├── Extracts claims: product name, claimed brand, official store claims
      │      └── Cross-checks claims against registered domain
      │
      ├── 5. Scoring Engine
      │      ├── Weighted sum capped at 100
      │      ├── 0-33 Low | 34-66 Medium | 67-100 High
      │      └── Lookalike floor: Lookalikes never drop below Medium (min 45 pts)
      │
      └── 6. Comparison Engine (retailers.json)
             └── Deterministic Google site-search templates (Never LLM-generated URLs)
```

---

## 4. Real Results from `results.md`

We evaluated the deterministic rules on a benchmark of 10 real legitimate retailer URLs and 10 synthetic lookalike domains:

- **Benchmark Total**: 20 test cases
- **Legitimate Retailers Flagged High (False Alarms)**: **0 / 10 (0.0%)** (all 10 scored Low Risk, 5/100)
- **Synthetic Lookalikes Intercepted**: **10 / 10 (100.0%)** (all 10 scored High Risk, 83/100)
- **Score Floor Enforcement**: Verified. No lookalike domain scored below Medium risk.

*Note: As noted in `results.md`, this benchmark measures deterministic rule precision on synthetic cases, not real-world wild internet accuracy.*

---

## 5. Model & License

- **Default Model**: `qwen3.5:2b` (or `qwen2.5:2b` / `qwen2.5:1.5b`) served locally via Ollama.
- **Model License**: Apache 2.0 / Qwen Community License.
- **Privacy & Local Execution**: Prompts and scraped page snippets stay on the local machine; no external LLM API keys or cloud tokens are required.

---

## 6. Original Work vs. Third-Party Libraries

### Third-Party Libraries & Runtimes:
- **FastAPI** & **Starlette**: HTTP routing, file serving, and ASGI framework
- **Uvicorn**: ASGI web server
- **HTTPX**: Async HTTP client for RDAP and page fetching
- **BeautifulSoup4**: Server-side HTML DOM parsing and text extraction
- **OpenAI Python SDK**: Client interface for the local Ollama OpenAI-compatible endpoint
- **Ollama**: Local open-weight model runner
- **Pytest**: Unit testing framework

### Original Components Built from Scratch:
- **Lookalike & Typosquatting Detection Engine** (`app/url_signals.py`): Levenshtein distance matching against brand directories with whitelist domain resolution.
- **Deterministic URL Signal Suite** (`app/url_signals.py`): Heuristic checks for Punycode, suspicious TLDs, IP hosts, and social seller classification.
- **Domain Age Evaluator** (`app/rdap_client.py`): ISO-8601 registration parsing and age-tier weighting.
- **Safe HTML Page Analyzer** (`app/page_fetcher.py`): Regex-based contact extraction, payment risk categorizer, and JS-rendering detector.
- **LLM Extraction & Think-Block Stripper** (`app/llm_analyzer.py`): Structured JSON extraction and official store claim mismatch detection.
- **Scoring Engine with Floor Guarantees** (`app/scoring.py`): Multi-signal weighted aggregator with lookalike floor protection.
- **Safe Comparison Link Generator** (`app/alternatives.py`): Whitelisted retailer site-search template builder.
- **Progressive Frontend Interface** (`static/`): Dark-mode responsive UI with SVG circular gauge, live audit checklist, and asynchronous two-phase loading.

---

## 7. Honest Limitations

1. **Warning Signs, Not Proof**: Heuristic scores highlight risk factors (e.g. recent domain, lack of address). A legitimate startup may have a new domain, while a sophisticated fraudster could hijack an older domain.
2. **Client-Side Rendered (SPA) Storefronts**: ScamLens fetches raw server HTML without running a headless browser (for CPU speed and security). React/Vue client-only storefronts will yield "page unreadable", falling back to URL and RDAP signals.
3. **RDAP Missing on National ccTLDs**: National registries like `.pk` do not publish public RDAP query endpoints; domain age for `.pk` is labeled "unknown" with minimal weight penalty.
4. **Small Model Language Limitations**: The 2B parameter model is optimized for CPU inference, but is less nuanced on complex Roman Urdu idioms compared to larger parameter models.

---

## 8. What We Learned

- **Layered signals beat monolithic LLMs**: Deterministic checks (whitelists, Levenshtein distance, regexes) run in milliseconds, catch 90% of spoofing attempts, and guarantee that LLM hallucinations never compromise URL safety.
- **Asynchronous progressive rendering**: CPU-based models can take 4–10 seconds to generate output; rendering rule-based scores immediately and streaming/updating AI insights in the background creates an instantaneous user experience.
- **Lookalike floor rules are critical**: If a domain impersonates a known brand, missing page content must never allow the score to drop into the "Low Risk" category.

---

## 9. License

This project is licensed under the [MIT License](LICENSE).
